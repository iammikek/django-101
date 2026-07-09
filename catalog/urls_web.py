"""URLs for the server-rendered shop frontend."""

from django.urls import path

from catalog.web_views import (
    ItemCreateView,
    ItemDetailView,
    ItemListView,
    ShopHomeView,
    ShopLoginView,
    ShopLogoutView,
    ShopRegisterView,
)

urlpatterns = [
    path("", ShopHomeView.as_view(), name="shop-home"),
    path("items/", ItemListView.as_view(), name="shop-item-list"),
    path("items/new/", ItemCreateView.as_view(), name="shop-item-create"),
    path("items/<int:pk>/", ItemDetailView.as_view(), name="shop-item-detail"),
    path("login/", ShopLoginView.as_view(), name="shop-login"),
    path("logout/", ShopLogoutView.as_view(), name="shop-logout"),
    path("register/", ShopRegisterView.as_view(), name="shop-register"),
]
