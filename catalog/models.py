"""Catalog models: categories and items."""

from django.db import models


class Category(models.Model):
    """Category table (FastAPI-101 Category equivalent)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    """Item table (FastAPI-101 Item equivalent)."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        db_index=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name
