"""
api/main.py
------------
This is the entry point of our API - the file we actually run to start
the server. It defines the "endpoints" (URLs) our API responds to.

RUN THIS FILE WITH:
    uvicorn api.main:app --reload
(explained in detail below)
"""

import os
import shutil
import uuid
from typing import List
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.models.schemas import (
    CustomerInput, PredictionOutput, HealthOutput,
    UserCreate, UserOut, Token, HistoryItem,
    BatchUploadResponse, BatchStatusResponse,
)
from api.services.predictor import predictor
from api.services import auth, cache
from api.services.batch_processor import process_batch
from api.db.database import Base, engine, get_db, SessionLocal
from api.db import models

# This creates all tables defined in db/models.py, IF they don't already
# exist. Running this every startup is safe - it won't wipe existing data
# or recreate tables that are already there.
Base.metadata.create_all(bind=engine)

# This creates our FastAPI application. Think of "app" as the whole
# restaurant - we'll now define what happens at each "counter" (endpoint).
app = FastAPI(
    title="Customer Churn Prediction API",
    description="Predicts whether a telecom customer is likely to churn.",
    version="1.0.0",
)


# ---------------------------------------------------------------------
# ENDPOINT 1: Health check
# ---------------------------------------------------------------------
# @app.get("/health") is called a "decorator" - it tells FastAPI:
# "whenever someone visits /health using a GET request, run the function
# right below this line."
#
# GET = "give me information" (used for reading/checking things)
# This endpoint doesn't take any input - it just confirms the API is alive
# and the model loaded correctly. Every real production API should have
# one of these - it's what monitoring tools "ping" to check if your
# service is up.
# ---------------------------------------------------------------------
@app.get("/health", response_model=HealthOutput)
def health_check():
    return {
        "status": "ok",
        "model_loaded": predictor.model is not None,
    }


# ---------------------------------------------------------------------
# ENDPOINT 2: Register a new user
# ---------------------------------------------------------------------
@app.post("/auth/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if this email is already taken
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password BEFORE saving - see auth.py for why
    new_user = models.User(
        email=user_in.email,
        hashed_password=auth.hash_password(user_in.password),
    )
    db.add(new_user)      # stage the new row
    db.commit()           # actually write it to the database (like SQL COMMIT)
    db.refresh(new_user)  # reload it so new_user.id gets filled in
    return new_user


# ---------------------------------------------------------------------
# ENDPOINT 3: Login - exchange email+password for a token
# ---------------------------------------------------------------------
# OAuth2PasswordRequestForm expects form data with fields "username" and
# "password" - this is a FastAPI/OAuth2 standard convention. We treat the
# "username" field as the email.
@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # "sub" (subject) is the standard JWT field name for "who is this token about"
    token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------
# ENDPOINT 4: Predict churn for one customer (now PROTECTED - requires login)
# ---------------------------------------------------------------------
# "current_user: models.User = Depends(auth.get_current_user)" means:
# before running this function, FastAPI must successfully verify the
# caller's token. If it fails, the caller gets a 401 error automatically,
# and this function's code never runs at all.
#
# We also now save every prediction to the database, linked to the user
# who made it - this is what powers the /history endpoint below.
# ---------------------------------------------------------------------
@app.post("/predict", response_model=PredictionOutput)
def predict_churn(
    customer: CustomerInput,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        customer_dict = customer.model_dump()

        # STEP 1: Check the "sticky note board" first - has this EXACT
        # customer profile been predicted recently? If so, skip the model
        # entirely and return instantly.
        cached_result = cache.get_cached_prediction(customer_dict)
        if cached_result:
            result = cached_result
            was_cached = "yes"
        else:
            result = predictor.predict(customer_dict)
            cache.set_cached_prediction(customer_dict, result)
            was_cached = "no"

        # Save this prediction to the database, tied to the logged-in user
        record = models.PredictionRecord(
            owner_id=current_user.id,
            contract=customer.Contract,
            tenure=customer.tenure,
            monthly_charges=customer.MonthlyCharges,
            churn_probability=result["churn_probability"],
            risk_level=result["risk_level"],
            from_cache=was_cached,
        )
        db.add(record)
        db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ---------------------------------------------------------------------
# ENDPOINT 6: Upload a CSV of many customers - PROCESSED IN THE BACKGROUND
# ---------------------------------------------------------------------
# This is the "smart waiter" pattern. Notice this function does NOT loop
# through every row itself - it just saves the file, creates a tracking
# row in the database, and hands the actual work off to BackgroundTasks,
# then returns IMMEDIATELY. The client doesn't sit there waiting.
# ---------------------------------------------------------------------
@app.post("/predict-batch", response_model=BatchUploadResponse)
def predict_batch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # Rate limit: at most 5 batch uploads per user per 60 seconds.
    # This protects the system from someone spamming huge uploads.
    if not cache.check_rate_limit(current_user.id, max_requests=5, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many batch uploads. Please wait a minute and try again.")

    # Save the uploaded file to a temp location on disk so our background
    # task can read it after this request has already finished
    os.makedirs("uploads", exist_ok=True)
    temp_path = f"uploads/{uuid.uuid4()}.csv"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create the tracking row - status starts as "processing"
    batch = models.PredictionBatch(owner_id=current_user.id, status="processing")
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Hand the real work off to run AFTER this response is sent.
    # We pass SessionLocal itself (not our current `db` session), because
    # this task runs later, possibly after `db` here has already closed.
    background_tasks.add_task(process_batch, batch.id, temp_path, current_user.id, SessionLocal)

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "message": "Batch accepted and is being processed. Poll /batch-status/{batch_id} for progress.",
    }


# ---------------------------------------------------------------------
# ENDPOINT 7: Check on a batch's progress
# ---------------------------------------------------------------------
@app.get("/batch-status/{batch_id}", response_model=BatchStatusResponse)
def batch_status(
    batch_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    batch = db.query(models.PredictionBatch).filter(models.PredictionBatch.id == batch_id).first()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    # Make sure users can only check THEIR OWN batches, not anyone else's
    if batch.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this batch")

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "total_rows": batch.total_rows,
        "processed_rows": batch.processed_rows,
        "failed_rows": batch.failed_rows,
        "error_message": batch.error_message,
    }


# ---------------------------------------------------------------------
# ENDPOINT 5: View my past predictions (also PROTECTED)
# ---------------------------------------------------------------------
@app.get("/history", response_model=List[HistoryItem])
def get_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # This is the ORM equivalent of:
    # SELECT * FROM prediction_records WHERE owner_id = <current_user.id>
    # ORDER BY created_at DESC;
    records = (
        db.query(models.PredictionRecord)
        .filter(models.PredictionRecord.owner_id == current_user.id)
        .order_by(models.PredictionRecord.created_at.desc())
        .all()
    )
    return records


# ---------------------------------------------------------------------
# ENDPOINT 3: Root - just a friendly welcome message
# ---------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Churn Prediction API is running. Visit /docs to try it out."}
