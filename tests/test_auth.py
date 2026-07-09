"""Integration tests for auth endpoints."""

from django.contrib.auth import get_user_model

User = get_user_model()


def test_register_user(client):
    response = client.post(
        "/auth/register",
        {"email": "alice@example.com", "password": "password123"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["email"] == "alice@example.com"
    assert "password" not in response.data


def test_register_duplicate_email(client, registered_user):
    response = client.post(
        "/auth/register",
        {"email": "test@example.com", "password": "secret123"},
        format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "USER_EMAIL_EXISTS"


def test_login_success(client, registered_user):
    response = client.post(
        "/auth/login",
        {"username": "test@example.com", "password": "secret123"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["token_type"] == "bearer"
    assert "access_token" in response.data


def test_login_invalid_password(client, registered_user):
    response = client.post(
        "/auth/login",
        {"username": "test@example.com", "password": "wrong-password"},
        format="json",
    )
    assert response.status_code == 401


def test_read_current_user(authed_client):
    response = authed_client.get("/auth/me")
    assert response.status_code == 200
    assert response.data["email"] == "test@example.com"


def test_read_current_user_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
