"""URL configuration for django-101."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from accounts.views import LoginView, MeView, RegisterView
from catalog.views import CategoryViewSet, ItemViewSet
from config.views import HealthView, RootView

router = DefaultRouter(trailing_slash=False)
router.register("items", ItemViewSet, basename="item")
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("", RootView.as_view()),
    path("health", HealthView.as_view()),
    path("openapi.json", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("shop/", include("catalog.urls_web")),
    path("admin/", admin.site.urls),
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/me", MeView.as_view()),
    path("", include(router.urls)),
]
