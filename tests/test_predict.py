"""
tests/test_predict.py
------------------------
Tests for /predict. This is where we confirm authentication actually
protects the endpoint (not just "seems to work when I tried it manually
that one time"), and that predictions come back in a sane shape.
"""


def test_predict_without_token_is_rejected(client, sample_customer):
    response = client.post("/predict", json=sample_customer)

    # No Authorization header was sent - this MUST fail
    assert response.status_code == 401


def test_predict_with_valid_token_succeeds(client, auth_headers, sample_customer):
    response = client.post("/predict", json=sample_customer, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "churn_probability" in data
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["risk_level"] in ["Low", "Medium", "High"]
    assert len(data["top_risk_factors"]) > 0


def test_predict_high_risk_profile_flagged_correctly(client, auth_headers):
    # A customer profile we KNOW should be high risk (from Day 1 testing):
    # month-to-month, brand new, no security add-ons
    high_risk_customer = {
        "gender": "Female", "SeniorCitizen": 0, "Partner": "Yes", "Dependents": "No",
        "tenure": 2, "PhoneService": "Yes", "MultipleLines": "No",
        "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
        "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
        "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check", "MonthlyCharges": 90.5, "TotalCharges": 181.0,
    }
    response = client.post("/predict", json=high_risk_customer, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["risk_level"] == "High"


def test_predict_with_missing_field_is_rejected(client, auth_headers):
    incomplete_customer = {"gender": "Female"}  # missing everything else

    response = client.post("/predict", json=incomplete_customer, headers=auth_headers)

    # Pydantic validation should catch this BEFORE it reaches our model
    assert response.status_code == 422


def test_predict_saves_to_history(client, auth_headers, sample_customer):
    client.post("/predict", json=sample_customer, headers=auth_headers)

    history_response = client.get("/history", headers=auth_headers)

    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["contract"] == sample_customer["Contract"]
