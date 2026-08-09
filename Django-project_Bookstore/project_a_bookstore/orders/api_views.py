from asyncio import start_unix_server

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from .permissions import IsOwner

from .models import Book, Order, OrderItem
from .serializers import CartItemSerializer, CartAddUpdateSerializer, OrderSerializer
from .cart import Cart


class CartViewSet(viewsets.ViewSet):
    """
    Кастомний ViewSet для керування кошиком у сесіях користувача.
    Не прив'язаний до моделі БД. Доступний усім користувачам (анонімним також).
    """

    permission_classes = [AllowAny]

    def list(self, request):
        """Отримання вмісту кошика (GET /api/cart/)."""
        cart = Cart(request)
        # формування списку елементів для CartItemSerializer
        cart_items = []
        for item in cart:
            cart_items.append(
                {
                    "book": item["book"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "total_price": item["total_price"],
                }
            )

        serializer = CartItemSerializer(cart_items, many=True)
        return Response(
            {"items": serializer.data, "total_cost": cart.get_total_price()}
        )

    @action(detail=False, methods=["post"], url_path="add")
    def add_item(self, request):
        """Додавання або оновлення товару в кошику (POST /api/cart/add/)."""
        serializer = CartAddUpdateSerializer(data=request.data)
        if serializer.is_valid():
            cart = Cart(request)
            book = Book.objects.get(pk=serializer.validated_data["book_id"])

            cart.add(
                book=book,
                quantity=serializer.validated_data["quantity"],
                override_quantity=serializer.validated_data["override_quantity"],
            )
            return Response(
                {"status": "Кошик оновлено успішно"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="remove")
    def remove_item(self, request):
        """Видалення товару з кошика повністю (POST /api/cart/remove/)."""
        book_id = request.data.get("book_id")
        if not book_id:
            return Response(
                {"error": "Параметр book_id обов'язковий"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            book = Book.objects.get(pk=book_id)
            cart = Cart(request)
            cart.remove(book)
            return Response(
                {"status": "Товар видалено з кошика"}, status=status.HTTP_200_OK
            )
        except Book.DoesNotExist:
            return Response(
                {"error": "Книгу не знайдено"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"], url_path="clear")
    def clear_cart(self, request):
        """Повне очищення кошика (POST /api/cart/clear/)."""
        cart = Cart(request)
        cart.clear()
        return Response({"status": "Кошик повністю очищено"}, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet для керування замовленнями в базі даних.

    * Перегляд списку та деталей доступний лише авторизованим користувачам (JWT).
    * Створення замовлення автоматично переносить товари з сесійного кошика.
    """

    serializer_class = OrderSerializer
    # Обмежуємо доступ, користувач повинен бути авторизований
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Користувач бачить ТІЛЬКИ свої замовлення, щоб ніхто не підглядів чужі чеки.
        Адміністратор (is_staff) бачить абсолютно всі замовлення в системі.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.prefetch_related("items__book").all()
        return Order.objects.prefetch_related("items__book").filter(email=user.email)

    def create(self, request, *args, **kwargs):
        """
        Кастомне створення замовлення (POST /api/orders/).
        Зчитує кошик користувача та оформлює транзакційну покупку.
        """
        cart = Cart(request)
        if not cart:
            return Response(
                {
                    "error": "Ваш кошик порожній. Немає товарів для оформлення замовлення."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # обертаємо всю логіку в атомарну транзакцію
        try:
            with transaction.atomic():
                # 1. Зберігаємо шапку замовлення
                order = serializer.save()

                # 2. Прохід по кошику, блокування залишків та створення OrderItem
                for item in cart:
                    book_id = item["book"].id
                    # Блокування рядків книги на рівні БД від Race Conditions
                    book = Book.objects.select_for_update().get(pk=book_id)

                    if book.stock < item["quantity"]:
                        raise ValueError(
                            f"Недостатньо товару '{book.title}' на складі. Доступно: {book.stock}"
                        )

                    # Зменшення кількості на складі
                    book.stock -= item["quantity"]
                    book.save()

                    # Створення позицій в чеку
                    OrderItem.objects.create(
                        order=order,
                        book=book,
                        price=item["price"],
                        quantity=item["quantity"],
                    )
                # 3. Очищення кошика після успішного замовлення
                cart.clear()

                # Повернення створеного замовлення
                return Response(
                    OrderSerializer(order).data, status=status.HTTP_201_CREATED
                )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
