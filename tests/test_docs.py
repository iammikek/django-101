"""OpenAPI schema and Swagger UI endpoints."""

import json


def test_openapi_schema(client):
    response = client.get("/openapi.json", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    schema = json.loads(response.content)
    assert schema["info"]["title"] == "django-101 API"
    paths = schema["paths"]
    assert "/items" in paths
    assert "/categories" in paths
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths


def test_swagger_ui(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"swagger" in response.content.lower()
