"""
tests/test_auth.py
--------------------
Tests for registration and login. Notice we test BOTH the "happy path"
(everything works correctly) AND the "unhappy paths" (things that SHOULD
fail, and we confirm they fail the right way). Good tests cover both -
untested failure cases are exactly where real bugs hide.
"""


def test_register_new_user_succeeds(client):
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "securepass123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    # Critical security check: the password must NEVER appear in the response
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    # Register once - should succeed
    client.post("/auth/register", json={"email": "dupe@example.com", "password": "pass123456"})

    # Register AGAIN with the same email - should be rejected
    response = client.post("/auth/register", json={"email": "dupe@example.com", "password": "differentpass"})

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_with_correct_credentials_returns_token(client):
    client.post("/auth/register", json={"email": "logintest@example.com", "password": "correctpass"})

    response = client.post(
        "/auth/login",
        data={"username": "logintest@example.com", "password": "correctpass"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_fails(client):
    client.post("/auth/register", json={"email": "wrongpass@example.com", "password": "correctpass"})

    response = client.post(
        "/auth/login",
        data={"username": "wrongpass@example.com", "password": "totally_wrong_password"},
    )

    assert response.status_code == 401


def test_login_with_nonexistent_email_fails(client):
    response = client.post(
        "/auth/login",
        data={"username": "doesnotexist@example.com", "password": "whatever"},
    )

    assert response.status_code == 401
