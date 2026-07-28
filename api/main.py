"""
api/main.py
------------
This is the entry point of our API - the file we actually run to start
the server. It defines the "endpoints" (URLs) our API responds to.

RUN THIS FILE WITH:
    uvicorn api.main:app --reload
(explained in detail below)
"""

from fastapi import FastAPI, HTTPException
from api.models.schemas import CustomerInput, PredictionOutput, HealthOutput
from api.services.predictor import predictor

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
# ENDPOINT 2: Predict churn for one customer
# ---------------------------------------------------------------------
# @app.post("/predict") means: whenever someone sends a POST request to
# /predict, run this function.
#
# POST = "here is data, please process it and do something" (used when
# sending data, unlike GET which just reads)
#
# "customer: CustomerInput" tells FastAPI: "expect the incoming request
# body to match the CustomerInput shape we defined in schemas.py, and
# automatically validate it before this function even runs."
# ---------------------------------------------------------------------
@app.post("/predict", response_model=PredictionOutput)
def predict_churn(customer: CustomerInput):
    try:
        # .model_dump() converts the validated Pydantic object back into
        # a plain Python dictionary, which is what our predictor expects
        result = predictor.predict(customer.model_dump())
        return result
    except Exception as e:
        # If anything goes wrong during prediction, we don't want the
        # server to crash or return a confusing raw error to the user.
        # HTTPException sends back a clean, proper error response instead.
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ---------------------------------------------------------------------
# ENDPOINT 3: Root - just a friendly welcome message
# ---------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Churn Prediction API is running. Visit /docs to try it out."}
