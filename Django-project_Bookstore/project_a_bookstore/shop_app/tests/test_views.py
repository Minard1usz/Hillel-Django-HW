from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from shop_app.models import Book, Category
from asgiref.sync import sync_to_async


class AsyncStoreViewTest(TestCase):

    async def test_store_view_without_cache(self):
        """Перевірка збору контексту з бази, коли кеш порожній"""
        await cache.aclear()

        response = await self.async_client.get(reverse("shop_app:store"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("special_offers", response.context)
        self.assertIn("categories", response.context)

    async def test_store_view_loads_fixtures_when_db_empty(self):
        """Перевірка логіки loaddata, якщо в базі немає жодної книги"""
        from shop_app.models import Book

        await cache.aclear()
        await sync_to_async(Book.objects.all().delete)()

        response = await self.async_client.get(reverse("shop_app:store"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(await Book.objects.aexists())

    async def test_store_view_authenticated_user(self):
        """Перевірка роботи view для залогіненого користувача"""
        from users.models import CustomUser

        user = await CustomUser.objects.acreate_user(
            username="testuser", password="password123"
        )
        await cache.aclear()

        # Використовуємо sync_to_async для авторизації
        await sync_to_async(self.client.force_login)(user)

        response = await self.async_client.get(reverse("shop_app:store"))

        self.assertEqual(response.status_code, 200)


class ShopViewsTests(TestCase):
    def setUp(self):
        # Створюємо тестові дані
        self.category = Category.objects.create(name="Фантастика")
        self.book = Book.objects.create(
            title="Тестова книга",
            author="Тестовий автор",
            description="Опис тестової книги",
            price=Decimal("150.00"),
            stock=10,
            category=self.category,
        )

    def test_book_list_view(self):
        """Тест сторінки зі списком товарів."""
        url = reverse("shop_app:book_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестова книга")

    def test_book_detail_view_success(self):
        """Тест сторінки деталей книги (існуюча книга)."""
        url = reverse("shop_app:book_detail", kwargs={"pk": self.book.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестова книга")

    def test_book_detail_view_not_found(self):
        """Тест сторінки деталей книги (неіснуюча книга — 404)."""
        url = reverse("shop_app:book_detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_book_list_by_category(self):
        """Тест фільтрації книг за категорією."""
        url = reverse("shop_app:book_list")
        response = self.client.get(url, {"category": self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Фантастика")
