"""
tests/conftest.py
-------------------
pytest automatically loads this file before running any tests. It's where
we set up things every test needs (called "fixtures" in pytest language).

WHY A SEPARATE TEST DATABASE?
We do NOT want our tests writing fake users/predictions into our real
PostgreSQL database - that would pollute real data. Instead, we point
tests at a lightweight in-memory SQLite database that exists only for the
few seconds each test runs, then disappears completely. This is a very
common real-world pattern: tests should never touch production data.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.db.database import Base, get_db
from api.services import cache as cache_module

# An in-memory SQLite database - exists only in RAM, gone the moment the
# test process ends. StaticPool keeps it alive across multiple connections
# within the same test (SQLite in-memory DBs are normally per-connection).
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """
    This REPLACES the real get_db dependency with one pointing at our
    test database, only during tests. The app code itself never knows
    the difference - it just asks for a db session via Depends(get_db).
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    """
    Gives each test a fresh TestClient with a clean, empty database AND
    a clean cache. Creates all tables before the test runs, and drops them
    after - so tests never affect each other or leave leftover data behind.

    IMPORTANT LESSON LEARNED: we also flush Redis before every test. Without
    this, a stale cached prediction from earlier MANUAL testing (through
    /docs, weeks ago) can silently mask a real bug - the test asks for a
    prediction, gets served an old cached answer instead of actually
    running the current code, and passes for the wrong reason. Tests must
    never share state with real, manually-generated data.
    """
    Base.metadata.create_all(bind=engine)
    cache_module.redis_client.flushdb()
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def auth_headers(client):
    """
    A reusable fixture: registers a test user, logs in, and returns
    ready-to-use auth headers - so tests that need a logged-in user don't
    have to repeat this setup every single time.
    """
    client.post("/auth/register", json={"email": "testuser@example.com", "password": "testpass123"})
    response = client.post(
        "/auth/login",
        data={"username": "testuser@example.com", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_customer():
    """A valid customer payload, reused across multiple tests."""
    return {
        "gender": "Female", "SeniorCitizen": 0, "Partner": "Yes", "Dependents": "No",
        "tenure": 2, "PhoneService": "Yes", "MultipleLines": "No",
        "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
        "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
        "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check", "MonthlyCharges": 90.5, "TotalCharges": 181.0,
    }
