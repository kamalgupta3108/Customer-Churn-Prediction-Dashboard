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


# --- Auth-related schemas (new for Day 3) ---

class UserCreate(BaseModel):
    """What a client must send to register a new account."""
    email: str
    password: str


class UserOut(BaseModel):
    """What we send BACK after registration - notice: no password field.
    We must never send password data back, even hashed."""
    id: int
    email: str

    model_config = {"from_attributes": True}  # lets us build this directly from a SQLAlchemy User object


class Token(BaseModel):
    """What we send back after a successful login - the 'wristband'."""
    access_token: str
    token_type: str = "bearer"


class HistoryItem(BaseModel):
    """One row of a user's past prediction history."""
    id: int
    contract: str
    tenure: int
    monthly_charges: float
    churn_probability: float
    risk_level: str

    model_config = {"from_attributes": True}


# --- Batch-related schemas (new for Day 4) ---

class BatchUploadResponse(BaseModel):
    """What we return immediately after accepting a CSV upload."""
    batch_id: int
    status: str
    message: str


class BatchStatusResponse(BaseModel):
    """What we return when checking on a batch's progress."""
    batch_id: int
    status: str
    total_rows: int
    processed_rows: int
    failed_rows: int
    error_message: str | None = None
