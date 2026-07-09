"""Tests for the server-rendered shop frontend."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture
def web_client() -> Client:
    return Client()


@pytest.fixture
def web_user(db) -> User:
    return User.objects.create_user(email="shopper@example.com", password="secret123")


def test_shop_home_renders(web_client):
    response = web_client.get("/shop/")
    assert response.status_code == 200
    assert b"Catalog Shop" in response.content
    assert b"Full-stack Django" in response.content


def test_shop_item_list_empty(web_client):
    response = web_client.get("/shop/items/")
    assert response.status_code == 200
    assert b"No items match" in response.content


def test_shop_item_detail(web_client, sample_item):
    response = web_client.get(f"/shop/items/{sample_item['id']}/")
    assert response.status_code == 200
    assert sample_item["name"].encode() in response.content


def test_shop_create_requires_login(web_client):
    response = web_client.get("/shop/items/new/")
    assert response.status_code == 302
    assert "/shop/login/" in response["Location"]


def test_shop_create_item(web_client, web_user, create_category):
    category = create_category()
    web_client.force_login(web_user)
    response = web_client.post(
        "/shop/items/new/",
        {
            "name": "Browser Widget",
            "description": "Added via HTML form",
            "price": "12.50",
            "category": category["id"],
        },
    )
    assert response.status_code == 302
    assert "/shop/items/" in response["Location"]

    detail = web_client.get(response["Location"])
    assert b"Browser Widget" in detail.content


def test_shop_login_page(web_client, web_user):
    response = web_client.get("/shop/login/")
    assert response.status_code == 200
    assert b"Browser session auth" in response.content

    logged_in = web_client.post(
        "/shop/login/",
        {"username": "shopper@example.com", "password": "secret123"},
    )
    assert logged_in.status_code == 302
    assert logged_in["Location"].endswith("/shop/")


def test_shop_register_page(web_client):
    response = web_client.get("/shop/register/")
    assert response.status_code == 200
    assert b"Create account" in response.content


def test_shop_register_creates_user_and_logs_in(web_client):
    response = web_client.post(
        "/shop/register/",
        {
            "email": "newshopper@example.com",
            "password1": "password123",
            "password2": "password123",
        },
    )
    assert response.status_code == 302
    assert response["Location"].endswith("/shop/")
    assert User.objects.filter(email="newshopper@example.com").exists()

    home = web_client.get("/shop/")
    assert b"newshopper@example.com" in home.content


def test_shop_register_duplicate_email(web_client, web_user):
    response = web_client.post(
        "/shop/register/",
        {
            "email": "shopper@example.com",
            "password1": "password123",
            "password2": "password123",
        },
    )
    assert response.status_code == 200
    assert b"already exists" in response.content
