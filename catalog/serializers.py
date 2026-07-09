"""DRF serializers for catalog API."""

from decimal import Decimal

from rest_framework import serializers

from catalog.models import Category, Item


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class ItemSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )
    category = CategorySerializer(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Item
        fields = ["id", "name", "description", "price", "category_id", "category"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["category_id"] = instance.category_id
        if isinstance(data.get("price"), Decimal):
            data["price"] = float(data["price"])
        return data


class ItemCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    category_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class ItemUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=255, required=False)
    description = serializers.CharField(required=False, allow_null=True)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01"), required=False
    )
    category_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class CategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100)
    description = serializers.CharField(required=False, allow_null=True)


class CategoryUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100, required=False)
    description = serializers.CharField(required=False, allow_null=True)


class CategoryItemStatsSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    item_count = serializers.IntegerField()
    average_price = serializers.FloatField()


class ItemStatsSerializer(serializers.Serializer):
    total_items = serializers.IntegerField()
    average_price = serializers.FloatField()
    min_price = serializers.FloatField(allow_null=True)
    max_price = serializers.FloatField(allow_null=True)
    uncategorized_count = serializers.IntegerField()
    by_category = CategoryItemStatsSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in ("average_price", "min_price", "max_price"):
            if data.get(key) is not None:
                data[key] = float(data[key])
        for row in data.get("by_category", []):
            row["average_price"] = float(row["average_price"])
        return data
