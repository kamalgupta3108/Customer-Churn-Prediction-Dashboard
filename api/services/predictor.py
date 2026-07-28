"""
api/services/predictor.py
--------------------------
This file's ONE job: load the saved model files from Day 1, and provide a
function that takes a customer's details and returns a churn prediction.

WHY A SEPARATE FILE FOR THIS?
In real projects, we keep "business logic" (the actual prediction work)
separate from "API routing" (which URL triggers which function). This way,
if we ever want to use this prediction logic somewhere else (a command-line
tool, a background job, a different API), we just import this file - we
don't need to touch any web/API code at all. This separation is called
"separation of concerns" - a term you'll hear a lot in real engineering
teams.
"""

import joblib
import json
import pandas as pd
from pathlib import Path

# Path to the model folder we created in Day 1.
# Path(__file__).parent... just means "figure out this file's own location,
# then go up to find the model folder" - so this works no matter which
# folder you run the server from.
MODEL_DIR = Path(__file__).resolve().parents[2] / "model"


class ChurnPredictor:
    """
    A class that loads all the saved Day 1 artifacts ONCE (when the server
    starts), and reuses them for every prediction request. This is
    important: loading a model from disk takes time, so we do NOT want to
    reload it on every single API call - that would make the API very slow.
    """

    def __init__(self):
        # Load everything we saved at the end of train.py
        self.model = joblib.load(MODEL_DIR / "churn_model.pkl")
        self.scaler = joblib.load(MODEL_DIR / "scaler.pkl")
        self.label_encoders = joblib.load(MODEL_DIR / "label_encoders.pkl")
        self.feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
        self.numeric_cols = joblib.load(MODEL_DIR / "numeric_cols.pkl")

        with open(MODEL_DIR / "metrics.json") as f:
            metrics = json.load(f)
        # Global top risk factors (from Day 1) - used to explain predictions
        # in a simple way. A more advanced version (future improvement)
        # would use SHAP to explain each INDIVIDUAL prediction, not just
        # show the same global factors every time.
        self.top_global_factors = list(metrics["top_risk_factors"].keys())[::-1]

        print(f"Model loaded successfully. Expecting {len(self.feature_cols)} features.")

    def _prepare_input(self, customer: dict) -> pd.DataFrame:
        """
        Takes a raw customer dictionary (like what arrives from the API
        request) and applies the EXACT SAME transformations we used during
        training in Day 1: label encoding categorical columns, then scaling
        numeric columns. This is critical - if we don't preprocess new data
        the same way we preprocessed training data, the model's predictions
        will be meaningless.
        """
        df = pd.DataFrame([customer])

        # Apply the SAME label encoders we saved from training.
        # We use .transform() (not .fit_transform()) because we're not
        # learning new categories here - we're reusing what was already
        # learned on the training data.
        for col, encoder in self.label_encoders.items():
            if col in df.columns:
                df[col] = encoder.transform(df[col])

        # Apply the SAME scaler we saved from training
        df[self.numeric_cols] = self.scaler.transform(df[self.numeric_cols])

        # Make sure columns are in the exact same order the model expects
        return df[self.feature_cols]

    def predict(self, customer: dict) -> dict:
        """
        The main function other code will call.
        Input: a dictionary of one customer's details.
        Output: a dictionary with the churn probability and risk level.
        """
        X = self._prepare_input(customer)

        # predict_proba returns [[prob_of_class_0, prob_of_class_1]]
        # class 1 = churn, so we grab index 1
        probability = float(self.model.predict_proba(X)[0][1])

        if probability >= 0.7:
            risk_level = "High"
        elif probability >= 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return {
            "churn_probability": round(probability, 3),
            "risk_level": risk_level,
            "top_risk_factors": self.top_global_factors[:5],
        }


# Create ONE shared instance when this file is first imported.
# main.py will import this same object, so the model is loaded only once
# when the server starts, not on every request.
predictor = ChurnPredictor()
