"""Catalog API viewsets."""

from decimal import Decimal, InvalidOperation

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from catalog.pagination import SkipLimitPagination
from catalog.serializers import (
    CategoryCreateSerializer,
    CategorySerializer,
    CategoryUpdateSerializer,
    ItemCreateSerializer,
    ItemSerializer,
    ItemStatsSerializer,
    ItemUpdateSerializer,
)
from catalog.services import CategoryService, ItemService
from catalog.throttles import WriteRateThrottle


class CategoryViewSet(viewsets.ViewSet):
    """Category CRUD (FastAPI-101 /categories equivalent)."""

    pagination_class = SkipLimitPagination

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_throttles(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [WriteRateThrottle()]
        return []

    def list(self, request):
        rows, total = CategoryService.list_categories(
            skip=int(request.query_params.get("skip", 0)),
            limit=min(max(int(request.query_params.get("limit", 10)), 1), 100),
        )
        serializer = CategorySerializer(rows, many=True)
        return Response(
            {
                "items": serializer.data,
                "total": total,
                "skip": int(request.query_params.get("skip", 0)),
                "limit": int(request.query_params.get("limit", 10)),
            }
        )

    def retrieve(self, request, pk=None):
        row = CategoryService.get_by_id(int(pk))
        return Response(CategorySerializer(row).data)

    def create(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = CategoryService.create(**serializer.validated_data)
        return Response(CategorySerializer(row).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        serializer = CategoryUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        row = CategoryService.update(int(pk), serializer.validated_data)
        return Response(CategorySerializer(row).data)

    def destroy(self, request, pk=None):
        CategoryService.delete(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ItemViewSet(viewsets.ViewSet):
    """Item CRUD + stats (FastAPI-101 /items equivalent)."""

    pagination_class = SkipLimitPagination

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_throttles(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [WriteRateThrottle()]
        return []

    def _parse_filters(self, request) -> dict:
        filters: dict = {}
        for param, key, parser in (
            ("min_price", "min_price", Decimal),
            ("max_price", "max_price", Decimal),
            ("category_id", "category_id", int),
            ("name_contains", "name_contains", str),
        ):
            raw = request.query_params.get(param)
            if raw is None:
                continue
            try:
                value = parser(raw)
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise ValidationError({param: ["Invalid value"]}) from exc
            if key in {"min_price", "max_price"} and value <= 0:
                raise ValidationError({param: ["Must be greater than 0"]})
            if key == "category_id" and value < 1:
                raise ValidationError({param: ["Must be >= 1"]})
            if key == "name_contains" and not (1 <= len(value) <= 255):
                raise ValidationError({param: ["Length must be 1-255"]})
            filters[key] = value
        return filters

    def list(self, request):
        try:
            skip = int(request.query_params.get("skip", 0))
            limit = int(request.query_params.get("limit", 10))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"detail": "Invalid pagination parameters"}) from exc
        if skip < 0:
            raise ValidationError({"skip": ["Must be >= 0"]})
        if limit < 1 or limit > 100:
            raise ValidationError({"limit": ["Must be between 1 and 100"]})

        filters = self._parse_filters(request)
        rows, total = ItemService.list_items(skip=skip, limit=limit, **filters)
        return Response(
            {
                "items": ItemSerializer(rows, many=True).data,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        )

    @action(detail=False, methods=["get"], url_path="stats/summary")
    def stats_summary(self, request):
        stats = ItemService.get_stats()
        serializer = ItemStatsSerializer(stats)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        row = ItemService.get_by_id(int(pk))
        return Response(ItemSerializer(row).data)

    def create(self, request):
        serializer = ItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = ItemService.create(**serializer.validated_data)
        return Response(ItemSerializer(row).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        serializer = ItemUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        row = ItemService.update(int(pk), serializer.validated_data)
        return Response(ItemSerializer(row).data)

    def destroy(self, request, pk=None):
        ItemService.delete(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)
