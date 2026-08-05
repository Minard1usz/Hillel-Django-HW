from rest_framework import serializers
from .models import Order, OrderItem
from shop_app.serializers import BookSerializer
from shop_app.models import Book


# Серіалізатори кошика / сесії
class CartItemSerializer(serializers.Serializer):
    """Серіалізатор для відображення одного елемента кошика (Read-only)"""

    book = BookSerializer(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )


class CartAddUpdateSerializer(serializers.Serializer):
    """Серіалізатор для додавання / зміни кількості товару в кошику (Write-only)"""

    book_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)
    override_quantity = serializers.BooleanField(default=False)

    def validate_book_id(self, value):
        """Перевірка, чи існує книга і чи є вона на складі"""
        try:
            book = Book.objects.get(pk=value)
        except Book.DoesNotExist:
            raise serializers.ValidationError("Такої книги не існує")
        return value


# Серіалізатори замовлень БД
class OrderItemSerializer(serializers.ModelSerializer):
    """Серіалізатор для елементів замовлення з вкладеними даними книги"""

    book_detail = BookSerializer(source="book", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "book", "book_detail", "price", "quantity", "get_cost"]
        read_only_fields = ["price"]


class OrderSerializer(serializers.ModelSerializer):
    """Головний серіалізатор для замовлення з вкладеними елементами."""

    items = OrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(
        source="get_total_cost", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "address",
            "postal_code",
            "city",
            "created",
            "updated",
            "paid",
            "stripe_id",
            "items",
            "total_cost",
        ]
        read_only_fields = ["paid", "stripe_id"]
