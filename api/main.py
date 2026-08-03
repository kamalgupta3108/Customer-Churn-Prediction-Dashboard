"""
api/main.py
------------
This is the entry point of our API - the file we actually run to start
the server. It defines the "endpoints" (URLs) our API responds to.

RUN THIS FILE WITH:
    uvicorn api.main:app --reload
(explained in detail below)
"""

from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.models.schemas import (
    CustomerInput, PredictionOutput, HealthOutput,
    UserCreate, UserOut, Token, HistoryItem,
)
from api.services.predictor import predictor
from api.services import auth
from api.db.database import Base, engine, get_db
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
        result = predictor.predict(customer.model_dump())

        # Save this prediction to the database, tied to the logged-in user
        record = models.PredictionRecord(
            owner_id=current_user.id,
            contract=customer.Contract,
            tenure=customer.tenure,
            monthly_charges=customer.MonthlyCharges,
            churn_probability=result["churn_probability"],
            risk_level=result["risk_level"],
        )
        db.add(record)
        db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


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
