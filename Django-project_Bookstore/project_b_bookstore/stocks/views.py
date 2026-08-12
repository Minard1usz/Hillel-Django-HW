from django.shortcuts import render
from django.db import transaction
from rest_framework import status, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from .models import Warehouse, Stock, StockMovement
from .serializers import (
    WarehouseSerializer,
    StockSerializer,
    ReserveStockSerializer,
    ReleaseStockSerializer,
)


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    """ "Для перегляду залишків на складі"""

    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [AllowAny]
    lookup_field = "book_id"


class ReserveStockView(views.APIView):
    """ "Резерв книги під замовлення з Project A"""

    permissions_classes = [AllowAny]

    @extend_schema(request=ReserveStockSerializer)
    def post(self, request):
        serializer = ReserveStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book_id = serializer.validated_data["book_id"]
        qty = serializer.validated_data["quantity"]
        order_id = serializer.validated_data["order_id"]

        with transaction.atomic():
            # Блокування рядка в БД, щоб уникнути race condtiion
            stock = Stock.objects.select_for_update().filter(book_id=book_id).first()

            if not stock:
                return Response(
                    {"error": f"Товар з book_id {book_id} не знайдено на складі"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if stock.available_quantity < qty:
                return Response(
                    {
                        "error": "Недостатньо товару на складі.",
                        "available": stock.available_quantity,
                        "requested": qty,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            # Оновлення резерву
            stock.reserved_quantity += qty
            stock.save()

            # Фіксування логу руху
            StockMovement.objects.create(
                stock=stock,
                movement_type=StockMovement.MovementType.RESERVE,
                quantity=qty,
                order_id=order_id,
            )

            return Response(
                {
                    "status": "reserved",
                    "book_id": book_id,
                    "reserved_quantity": qty,
                    "remaining_available": stock.available_quantity,
                },
                status=status.HTTP_200_OK,
            )


class ReleaseStockView(views.APIView):
    """Знімаємо резерв книги (наприклад, при скасуванні замовлення)"""

    permission_classes = [AllowAny]

    @extend_schema(request=ReleaseStockSerializer)
    def post(self, request):
        serializer = ReleaseStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book_id = serializer.validated_data["book_id"]
        qty = serializer.validated_data["quantity"]
        order_id = serializer.validated_data["order_id"]

        with transaction.atomic():
            stock = Stock.objects.select_for_update().filter(book_id=book_id).first()

            if not stock:
                return Response(
                    {"error": "Товар не знайдено"}, status=status.HTTP_404_NOT_FOUND
                )

            # Зняття резерву (не менше 0)
            stock.reserved_quantity = max(0, stock.reserved_quantity - qty)
            stock.save()

            StockMovement.objects.create(
                stock=stock,
                movement_type=StockMovement.MovementType.RELEASE,
                quantity=qty,
                order_id=order_id,
            )

            return Response(
                {
                    "status": "released",
                    "book_id": book_id,
                    "released_quantity": qty,
                    "remaining_available": stock.available_quantity,
                },
                status=status.HTTP_200_OK,
            )
