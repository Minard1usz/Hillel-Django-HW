from django.contrib import admin
from .models import Warehouse, Stock, StockMovement


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "warehouse",
        "book_id",
        "quantity",
        "reserved_quantity",
        "available_quantity",
        "updated_at",
    )
    list_filter = ("warehouse",)
    search_fields = ("book_id",)
    readonly_fields = ("updated_at",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stock",
        "movement_type",
        "quantity",
        "order_id",
        "created_at",
    )
    list_filter = ("movement_type", "created_at")
    search_fields = ("stock__book_id", "order_id")
    readonly_fields = ("created_at",)
