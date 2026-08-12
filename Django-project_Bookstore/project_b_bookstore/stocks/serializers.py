from rest_framework import serializers
from .models import Warehouse, Stock, StockMovement


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "address", "is_active"]


class StockSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Stock
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "book_id",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "updated_at",
        ]


class ReserveStockSerializer(serializers.Serializer):
    book_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    order_id = serializers.IntegerField(min_value=1)


class ReleaseStockSerializer(serializers.Serializer):
    book_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    order_id = serializers.IntegerField(min_value=1)
