"""Integration tests for items API."""

import pytest


def test_list_items_empty(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert response.data == {"items": [], "total": 0, "skip": 0, "limit": 10}


def test_create_item(authed_client):
    response = authed_client.post(
        "/items",
        {"name": "Widget", "description": "A nice widget", "price": "9.99"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "Widget"
    assert response.data["price"] == 9.99


def test_create_item_without_auth(client):
    response = client.post("/items", {"name": "Thing", "price": "5.00"}, format="json")
    assert response.status_code == 401


def test_create_item_with_category(authed_client, create_category):
    category = create_category(name="Electronics")
    response = authed_client.post(
        "/items",
        {"name": "Gadget", "price": "15.00", "category_id": category["id"]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["category"]["name"] == "Electronics"


def test_get_items_stats(client, authed_client, create_item):
    create_item(name="A", price="10.00")
    response = client.get("/items/stats/summary")
    assert response.status_code == 200
    assert response.data["total_items"] == 1


def test_list_items_filter_by_min_price(client, authed_client, create_item):
    create_item(name="Cheap", price="5.00")
    create_item(name="Pricey", price="20.00")
    response = client.get("/items?min_price=10")
    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["items"][0]["name"] == "Pricey"


@pytest.mark.parametrize(
    "query",
    ["limit=101", "skip=-1", "min_price=-1"],
)
def test_list_items_validation_errors(client, query):
    response = client.get(f"/items?{query}")
    assert response.status_code == 422
