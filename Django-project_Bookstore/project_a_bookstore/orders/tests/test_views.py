from unittest.mock import patch
import requests
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from orders.services import WarehouseService, WarehouseServiceError
from shop_app.models import Book, Category

User = get_user_model()


class OrdersLogicTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

        self.category = Category.objects.create(
            name="Fiction",
        )

        self.book = Book.objects.create(
            title="Test Book",
            category=self.category,
            price=100.00,
            stock=10,
        )

    # === ТЕСТИ ДЛЯ РЕЗЕРВУВАННЯ СКТАДУ (SERVICES.PY) ===

    @patch("orders.services.requests.post")
    def test_warehouse_service_reserve_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "reserved"}

        res = WarehouseService.reserve_stock(
            book_id=self.book.id, quantity=2, order_id=1
        )
        self.assertEqual(res, {"status": "reserved"})

    @patch("orders.services.requests.post")
    def test_warehouse_service_reserve_failure(self, mock_post):
        mock_post.return_value.status_code = 409
        mock_post.return_value.json.return_value = {
            "error": "Недостатньо товару на складі."
        }

        with self.assertRaises(WarehouseServiceError):
            WarehouseService.reserve_stock(
                book_id=self.book.id, quantity=100, order_id=1
            )

    @patch("orders.services.requests.post")
    def test_warehouse_reserve_404(self, mock_post):
        mock_post.return_value.status_code = 404
        with self.assertRaises(WarehouseServiceError):
            WarehouseService.reserve_stock(book_id=999, quantity=1, order_id=1)

    @patch("orders.services.requests.post")
    def test_warehouse_reserve_500(self, mock_post):
        mock_post.return_value.status_code = 500
        with self.assertRaises(WarehouseServiceError):
            WarehouseService.reserve_stock(book_id=self.book.id, quantity=1, order_id=1)

    @patch("orders.services.requests.post")
    def test_warehouse_reserve_network_exception(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        with self.assertRaises(WarehouseServiceError):
            WarehouseService.reserve_stock(book_id=self.book.id, quantity=1, order_id=1)

    @patch("orders.services.requests.post")
    def test_warehouse_release_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "released"}
        res = WarehouseService.release_stock(
            book_id=self.book.id, quantity=1, order_id=1
        )
        self.assertEqual(res, {"status": "released"})

    @patch("orders.services.requests.post")
    def test_warehouse_release_failure(self, mock_post):
        mock_post.return_value.status_code = 500
        with self.assertRaises(WarehouseServiceError):
            WarehouseService.release_stock(book_id=self.book.id, quantity=1, order_id=1)

    @patch("orders.services.requests.post")
    def test_warehouse_release_network_exception(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        with self.assertRaises(WarehouseServiceError):
            WarehouseService.release_stock(book_id=self.book.id, quantity=1, order_id=1)

    # === ТЕСТИ ДЛЯ КОРЗИНИ ТА СТВОРЕННЯ ЗАМОВЛЕННЯ (VIEWS.PY) ===

    def test_cart_add_and_remove(self):
        response = self.client.post(
            reverse("orders:cart_add", args=[self.book.id]),
            {"quantity": 2, "override": False},
        )
        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertIn(str(self.book.id), session.get("cart", {}))

        response = self.client.post(
            reverse("orders:cart_remove", args=[self.book.id]),
        )
        self.assertEqual(response.status_code, 302)

    def test_cart_detail_view_authenticated_async(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("orders:cart_detail"))
        self.assertEqual(response.status_code, 200)

    @patch("orders.services.WarehouseService.reserve_stock")
    def test_order_create_view_post(self, mock_reserve):
        mock_reserve.return_value = {"status": "reserved"}

        session = self.client.session
        session["cart"] = {str(self.book.id): {"quantity": 1, "price": "100.00"}}
        session.save()

        response = self.client.post(
            reverse("orders:order_create"),
            {
                "first_name": "Yevhen",
                "last_name": "Dev",
                "email": "yevhen@example.com",
                "address": "Main St 1",
                "postal_code": "49000",
                "city": "Dnipro",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

    @patch("orders.services.WarehouseService.reserve_stock")
    def test_order_create_view_warehouse_error(self, mock_reserve):
        mock_reserve.side_effect = WarehouseServiceError("Немає на складі")

        session = self.client.session
        session["cart"] = {str(self.book.id): {"quantity": 100, "price": "100.00"}}
        session.save()

        response = self.client.post(
            reverse("orders:order_create"),
            {
                "first_name": "Yevhen",
                "last_name": "Dev",
                "email": "yevhen@example.com",
                "address": "Main St 1",
                "postal_code": "49000",
                "city": "Dnipro",
            },
        )
        self.assertEqual(response.status_code, 200)

    # === ТЕСТИ ДЛЯ STRIPE-ОПЛАТИ (VIEWS.PY) ===

    def test_payment_completed_view(self):
        response = self.client.get(reverse("orders:payment_completed"))
        self.assertEqual(response.status_code, 200)

    @patch("orders.services.WarehouseService.release_stock")
    def test_payment_canceled_view(self, mock_release):
        mock_release.return_value = {"status": "released"}

        order = Order.objects.create(
            first_name="Yevhen", email="yevhen@example.com", paid=False
        )
        OrderItem.objects.create(
            order=order, book=self.book, price=self.book.price, quantity=1
        )

        session = self.client.session
        session["order_id"] = order.id
        session.save()

        response = self.client.get(reverse("orders:payment_canceled"))
        self.assertEqual(response.status_code, 200)
        mock_release.assert_called_once()

    @patch("stripe.checkout.Session.create")
    def test_payment_process_view(self, mock_stripe):
        mock_stripe.return_value = type(
            "StripeSession", (), {"id": "cs_test_123", "url": "https://stripe.com/pay"}
        )()

        order = Order.objects.create(
            first_name="Yevhen", email="yevhen@example.com", paid=False
        )
        OrderItem.objects.create(
            order=order, book=self.book, price=self.book.price, quantity=1
        )

        session = self.client.session
        session["order_id"] = order.id
        session.save()

        response = self.client.get(reverse("orders:payment_process"))
        self.assertIn(response.status_code, [200, 302])

    def test_order_create_view_get(self):
        """Тест відображення сторінки з формою створення замовлення (GET)."""
        session = self.client.session
        session["cart"] = {str(self.book.id): {"quantity": 1, "price": "100.00"}}
        session.save()

        response = self.client.get(reverse("orders:order_create"))
        self.assertEqual(response.status_code, 200)

    def test_order_create_view_invalid_form(self):
        """Тест відправки невалідної форми замовлення (POST з порожніми полями)."""
        session = self.client.session
        session["cart"] = {str(self.book.id): {"quantity": 1, "price": "100.00"}}
        session.save()

        # Отримання порожніх даних
        response = self.client.post(reverse("orders:order_create"), {})
        # Повернення форми зі значенням 200 та помилками валідації
        self.assertEqual(response.status_code, 200)

    def test_order_create_view_empty_cart(self):
        """Тест спроби створити замовлення з порожнім кошиком."""
        session = self.client.session
        session["cart"] = {}
        session.save()

        response = self.client.get(reverse("orders:order_create"))
        # Перенаправлення на кошик  або головну сторінку
        self.assertIn(response.status_code, [302, 200])

    def test_payment_process_no_order_in_session(self):
        """Тест спроби перейти на оплату без order_id в сесії."""
        session = self.client.session
        if "order_id" in session:
            del session["order_id"]
            session.save()

        response = self.client.get(reverse("orders:payment_process"))
        # Редірект або 404/400
        self.assertIn(response.status_code, [302, 404, 400])
