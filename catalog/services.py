"""Service layer: business logic separated from API views."""

from decimal import Decimal

from django.db import connection
from django.db.models import Avg, Count, Max, Min

from catalog.exceptions import (
    CategoryInUseError,
    CategoryNameExistsError,
    CategoryNotFoundError,
    ItemNotFoundError,
)
from catalog.models import Category, Item


class CategoryService:
    """Service class for category business logic."""

    @staticmethod
    def list_categories(skip: int, limit: int) -> tuple[list[Category], int]:
        queryset = Category.objects.all()
        total = queryset.count()
        rows = list(queryset[skip : skip + limit])
        return rows, total

    @staticmethod
    def get_by_id(category_id: int) -> Category:
        try:
            return Category.objects.get(pk=category_id)
        except Category.DoesNotExist as exc:
            raise CategoryNotFoundError() from exc

    @staticmethod
    def _ensure_unique_name(name: str, category_id: int | None = None) -> None:
        queryset = Category.objects.filter(name=name)
        if category_id is not None:
            queryset = queryset.exclude(pk=category_id)
        if queryset.exists():
            raise CategoryNameExistsError(name)

    @staticmethod
    def create(name: str, description: str | None = None) -> Category:
        CategoryService._ensure_unique_name(name)
        return Category.objects.create(name=name, description=description)

    @staticmethod
    def update(category_id: int, data: dict) -> Category:
        row = CategoryService.get_by_id(category_id)
        if "name" in data:
            CategoryService._ensure_unique_name(data["name"], category_id=category_id)
        for field, value in data.items():
            setattr(row, field, value)
        row.save()
        return row

    @staticmethod
    def delete(category_id: int) -> None:
        row = CategoryService.get_by_id(category_id)
        if Item.objects.filter(category_id=category_id).exists():
            raise CategoryInUseError()
        row.delete()


class ItemService:
    """Service class for item business logic."""

    @staticmethod
    def _validate_category_id(category_id: int | None) -> None:
        if category_id is not None:
            CategoryService.get_by_id(category_id)

    @staticmethod
    def _items_queryset(
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        category_id: int | None = None,
        name_contains: str | None = None,
    ):
        queryset = Item.objects.select_related("category").all()
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if name_contains is not None:
            queryset = queryset.filter(name__icontains=name_contains)
        return queryset

    @staticmethod
    def list_items(
        skip: int,
        limit: int,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        category_id: int | None = None,
        name_contains: str | None = None,
    ) -> tuple[list[Item], int]:
        queryset = ItemService._items_queryset(
            min_price=min_price,
            max_price=max_price,
            category_id=category_id,
            name_contains=name_contains,
        )
        total = queryset.count()
        rows = list(queryset[skip : skip + limit])
        return rows, total

    @staticmethod
    def get_by_id(item_id: int) -> Item:
        try:
            return Item.objects.select_related("category").get(pk=item_id)
        except Item.DoesNotExist as exc:
            raise ItemNotFoundError() from exc

    @staticmethod
    def create(
        name: str,
        price: Decimal,
        description: str | None = None,
        category_id: int | None = None,
    ) -> Item:
        ItemService._validate_category_id(category_id)
        item = Item.objects.create(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
        )
        return ItemService.get_by_id(item.id)

    @staticmethod
    def update(item_id: int, data: dict) -> Item:
        row = ItemService.get_by_id(item_id)
        if "category_id" in data:
            ItemService._validate_category_id(data["category_id"])
        for field, value in data.items():
            setattr(row, field, value)
        row.save()
        return ItemService.get_by_id(item_id)

    @staticmethod
    def delete(item_id: int) -> None:
        row = ItemService.get_by_id(item_id)
        row.delete()

    @staticmethod
    def get_stats() -> dict:
        count = Item.objects.count()
        if count == 0:
            return {
                "total_items": 0,
                "average_price": Decimal("0.00"),
                "min_price": None,
                "max_price": None,
                "uncategorized_count": 0,
                "by_category": [],
            }

        aggregates = Item.objects.aggregate(
            avg_price=Avg("price"),
            min_price=Min("price"),
            max_price=Max("price"),
        )
        uncategorized_count = Item.objects.filter(category__isnull=True).count()

        category_rows = (
            Category.objects.filter(items__isnull=False)
            .annotate(item_count=Count("items"), average_price=Avg("items__price"))
            .order_by("name")
        )
        by_category = [
            {
                "category_id": row.id,
                "category_name": row.name,
                "item_count": row.item_count,
                "average_price": Decimal(str(round(float(row.average_price), 2))),
            }
            for row in category_rows
        ]

        return {
            "total_items": count,
            "average_price": Decimal(str(round(float(aggregates["avg_price"]), 2))),
            "min_price": aggregates["min_price"],
            "max_price": aggregates["max_price"],
            "uncategorized_count": uncategorized_count,
            "by_category": by_category,
        }

    @staticmethod
    def check_database() -> None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
