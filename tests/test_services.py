"""Service layer unit tests."""

from decimal import Decimal

import pytest

from catalog.exceptions import CategoryInUseError, CategoryNameExistsError, ItemNotFoundError
from catalog.services import CategoryService, ItemService


@pytest.mark.django_db
def test_category_duplicate_name():
    CategoryService.create("Tools", None)
    with pytest.raises(CategoryNameExistsError):
        CategoryService.create("Tools", None)


@pytest.mark.django_db
def test_delete_category_in_use():
    category = CategoryService.create("Busy", None)
    ItemService.create("Hammer", Decimal("9.99"), category_id=category.id)
    with pytest.raises(CategoryInUseError):
        CategoryService.delete(category.id)


@pytest.mark.django_db
def test_item_get_by_id_not_found():
    with pytest.raises(ItemNotFoundError):
        ItemService.get_by_id(999)


@pytest.mark.django_db
def test_item_stats_by_category():
    electronics = CategoryService.create("Electronics", None)
    ItemService.create("Phone", Decimal("100.00"), category_id=electronics.id)
    ItemService.create("Loose", Decimal("5.00"))
    stats = ItemService.get_stats()
    assert stats["total_items"] == 2
    assert stats["uncategorized_count"] == 1
    assert len(stats["by_category"]) == 1
