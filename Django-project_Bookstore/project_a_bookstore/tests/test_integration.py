# для user flows
import pytest
from unittest.mock import patch
from django.urls import reverse
from .factories import BookFactory, CategoryFactory
from orders.models import Order


# -----------------------------------------------------------------------------
# СЦЕНАРІЙ 1: Повний шлях звичайного покупця
# -----------------------------------------------------------------------------
@patch("orders.views.WarehouseService.reserve_stock")
@pytest.mark.django_db
def test_customer_successful_purchase_flow(mock_reserve, client):
    # Заглушка складського сервісу: вдале резервування
    mock_reserve.return_value = True

    book = BookFactory(title="Ефективний Python", price=450.00, stock=10)

    # 1. Перегляд каталогу
    response = client.get(reverse("shop_app:book_list"))
    assert response.status_code == 200
    assert book.title in response.content.decode("utf-8")

    # 2. Деталі книги
    response = client.get(reverse("shop_app:book_detail", kwargs={"pk": book.pk}))
    assert response.status_code == 200

    # 3. Додаємо в кошик через POST
    client.post(
        reverse("orders:cart_add", kwargs={"book_id": book.id}),
        data={"quantity": 2, "override": False},
    )

    # 4. Оформлюємо замовлення
    order_data = {
        "first_name": "Алекс",
        "last_name": "Тестер",
        "email": "alex@example.com",
        "address": "Шевченко 7",
        "city": "Дніпро",
        "postal_code": "49000",
    }
    response = client.post(reverse("orders:order_create"), data=order_data)

    # 5. Успіх! Перевіряємо редірект та наявність у БД
    assert response.status_code in [200, 302]
    assert Order.objects.filter(email="alex@example.com").exists()


# -----------------------------------------------------------------------------
# СЦЕНАРІЙ 2: Купівля декількох книг
# -----------------------------------------------------------------------------
@patch("orders.views.WarehouseService.reserve_stock")
@pytest.mark.django_db
def test_customer_multiple_items_purchase_flow(mock_reserve, client):
    mock_reserve.return_value = True

    book1 = BookFactory(title="Книга 1", price=200.00, stock=5)
    book2 = BookFactory(title="Книга 2", price=300.00, stock=5)

    client.post(
        reverse("orders:cart_add", kwargs={"book_id": book1.id}),
        data={"quantity": 1, "override": False},
    )
    client.post(
        reverse("orders:cart_add", kwargs={"book_id": book2.id}),
        data={"quantity": 2, "override": False},
    )

    order_data = {
        "first_name": "Юрій",
        "last_name": "Потужний",
        "email": "uri@example.com",
        "address": "Центральна 1",
        "city": "Харків",
        "postal_code": "61000",
    }
    response = client.post(reverse("orders:order_create"), data=order_data)

    assert response.status_code in [200, 302]
    assert Order.objects.filter(email="uri@example.com").exists()


# -----------------------------------------------------------------------------
# СЦЕНАРІЙ 3: Невдале оформлення через невалідні дані
# -----------------------------------------------------------------------------
@patch("orders.views.WarehouseService.reserve_stock")
@pytest.mark.django_db
def test_customer_failed_validation_flow(mock_reserve, client):
    mock_reserve.return_value = True

    book = BookFactory(title="Django для профі", price=500.00, stock=5)

    client.post(
        reverse("orders:cart_add", kwargs={"book_id": book.id}),
        data={"quantity": 1, "override": False},
    )

    bad_order_data = {
        "first_name": "",
        "last_name": "Бот",
        "email": "no-email",
        "address": "вулиця 404",
        "city": "Львів",
        "postal_code": "79000",
    }
    response = client.post(reverse("orders:order_create"), data=bad_order_data)

    assert response.status_code == 200
    assert "form" in response.context
    assert not response.context["form"].is_valid()
    assert "first_name" in response.context["form"].errors
    assert "email" in response.context["form"].errors
    assert not Order.objects.filter(email="no-email").exists()
