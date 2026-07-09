"""Integration tests for categories API."""


def test_list_categories_empty(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.data["items"] == []


def test_create_category(authed_client):
    response = authed_client.post(
        "/categories",
        {"name": "Tools", "description": "Hand tools"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "Tools"


def test_create_category_without_auth(client):
    response = client.post("/categories", {"name": "Tools"}, format="json")
    assert response.status_code == 401


def test_delete_category_in_use(authed_client, create_category, create_item):
    category = create_category(name="Busy")
    create_item(category_id=category["id"])
    response = authed_client.delete(f"/categories/{category['id']}")
    assert response.status_code == 409
    assert response.data["code"] == "CATEGORY_IN_USE"
