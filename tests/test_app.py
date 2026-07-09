"""Health and root endpoints."""


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.data["message"] == "Hello from Django!"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == {"status": "ok", "database": "connected"}
