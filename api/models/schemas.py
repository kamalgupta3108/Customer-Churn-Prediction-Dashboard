"""
api/models/schemas.py
----------------------
This file defines the SHAPE of data going in and out of our API, using
Pydantic (a library FastAPI is built on top of).

WHY DO WE NEED THIS?
Without it, anyone could send our API garbage data - a typo'd field name,
a number where we expect text, a missing field - and our code would likely
crash with a confusing error, or worse, silently give a wrong prediction.

Pydantic checks the incoming data BEFORE our code even runs, and if
something's wrong, it automatically sends back a clear error message like
"tenure: field required" instead of a crash. This is called "validation."
"""

from pydantic import BaseModel, Field
from typing import List


class CustomerInput(BaseModel):
    """
    This describes exactly what one customer's data must look like for a
    prediction request. Every field here matches a column from our Day 1
    training data.
    """
    gender: str = Field(..., examples=["Male"])
    SeniorCitizen: int = Field(..., ge=0, le=1, description="0 = No, 1 = Yes")
    Partner: str = Field(..., examples=["Yes"])
    Dependents: str = Field(..., examples=["No"])
    tenure: int = Field(..., ge=0, description="Number of months as a customer")
    PhoneService: str = Field(..., examples=["Yes"])
    MultipleLines: str = Field(..., examples=["No"])
    InternetService: str = Field(..., examples=["Fiber optic"])
    OnlineSecurity: str = Field(..., examples=["No"])
    OnlineBackup: str = Field(..., examples=["Yes"])
    DeviceProtection: str = Field(..., examples=["No"])
    TechSupport: str = Field(..., examples=["No"])
    StreamingTV: str = Field(..., examples=["Yes"])
    StreamingMovies: str = Field(..., examples=["No"])
    Contract: str = Field(..., examples=["Month-to-month"])
    PaperlessBilling: str = Field(..., examples=["Yes"])
    PaymentMethod: str = Field(..., examples=["Electronic check"])
    MonthlyCharges: float = Field(..., ge=0)
    TotalCharges: float = Field(..., ge=0)

    # This just tells FastAPI's auto-generated docs what a sample request
    # looks like - purely for the /docs page, doesn't affect logic.
    model_config = {
        "json_schema_extra": {
            "example": {
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "tenure": 5,
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "InternetService": "Fiber optic",
                "OnlineSecurity": "No",
                "OnlineBackup": "No",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "Yes",
                "StreamingMovies": "Yes",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 85.5,
                "TotalCharges": 420.75,
            }
        }
    }


class PredictionOutput(BaseModel):
    """This describes exactly what our API sends BACK after a prediction."""
    churn_probability: float
    risk_level: str
    top_risk_factors: List[str]


class HealthOutput(BaseModel):
    """Simple response for our /health endpoint."""
    status: str
    model_loaded: bool
