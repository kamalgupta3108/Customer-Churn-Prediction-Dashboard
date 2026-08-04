"""
tests/test_health.py
----------------------
The simplest possible test, to get comfortable with the pattern.

pytest automatically finds any function starting with "test_" in any file
starting with "test_", and runs it. `assert` is the core of every test:
"I assert this thing is true - if it's not, fail the test and tell me."
"""


def test_health_check_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_loaded"] is True


def test_root_endpoint_responds(client):
    response = client.get("/")
    assert response.status_code == 200
