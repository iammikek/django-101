"""Shared pytest fixtures."""

from collections.abc import Callable
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@pytest.fixture(autouse=True)
def _enable_db(db):
    """Enable database access for all tests."""


@pytest.fixture(autouse=True)
def throttle_setting(request, settings):
    """Use generous rate limits unless @pytest.mark.rate_limit."""
    if request.node.get_closest_marker("rate_limit"):
        yield
        return
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {"auth": "10000/minute", "writes": "10000/minute"},
    }
    yield


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def registered_user(client) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        {"email": "test@example.com", "password": "secret123"},
        format="json",
    )
    assert response.status_code == 201
    return response.data


@pytest.fixture
def authed_client(client, registered_user) -> APIClient:
    user = User.objects.get(email="test@example.com")
    token = str(AccessToken.for_user(user))
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def create_category(authed_client) -> Callable[..., dict[str, Any]]:
    def _create_category(**overrides: Any) -> dict[str, Any]:
        payload = {"name": "Tools", **overrides}
        response = authed_client.post("/categories", payload, format="json")
        assert response.status_code == 201
        return response.data

    return _create_category


@pytest.fixture
def create_item(authed_client) -> Callable[..., dict[str, Any]]:
    def _create_item(**overrides: Any) -> dict[str, Any]:
        payload = {"name": "Widget", "price": "9.99", **overrides}
        response = authed_client.post("/items", payload, format="json")
        assert response.status_code == 201
        return response.data

    return _create_item


@pytest.fixture
def sample_item(create_item) -> dict[str, Any]:
    return create_item()
