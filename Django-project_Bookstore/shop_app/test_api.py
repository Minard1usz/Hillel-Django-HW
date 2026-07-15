from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from shop_app.models import Book, Category
from orders.models import Order

User = get_user_model()

class StoreAPITestCase(APITestCase):
    def setUp(self):
        # Створення користувачів
        self.user = User.objects.create_user(username='user', email='user@test.com', password='password123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='password123')

        # Створення БД
        self.category = Category.objects.create(name='Sci-Fi', slug='sci-fi')
        self.book1 = Book.objects.create(
            title='Dune', author='Frank Herbert', price=250.00, stock=10, category=self.category
        )
        self.book2 = Book.objects.create(
            title='Hobbit', author='J.R.R. Tolkien', price=180.00, stock=5, category=self.category
        )

        # Маршрути
        self.books_url = '/api/v1/books/'
        self.categories_url = '/api/v1/categories/'
        self.token_url = reverse('token_obtain_pair')

    # Тести JWT автентифікації (5 тестів)
    def test_jwt_obtain_token_success(self):
        """1. Успішне отримання токена за правильними кредами."""
        response = self.client.post(self.token_url, {'username': 'user', 'password': 'password123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_obtain_token_invalid_password(self ):
        """2. Помилка авторизації при неправильному паролі."""
        response = self.client.post(self.token_url, {'username': 'user', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_verify(self):
        """3. Перевірка валідності отриманого токена."""
        token_res = self.client.post(self.token_url, {'username': 'user', 'password': 'password123'})
        verify_url = reverse('token_verify')
        response = self.client.post(verify_url, {'token': token_res.data['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jwt_token_refresh(self):
        """4. Оновлення access токена через refresh токен."""
        token_res = self.client.post(self.token_url, {'username': 'user', 'password': 'password123'})
        refresh_url = reverse('token_refresh')
        response = self.client.post(refresh_url, {'refresh': token_res.data['refresh']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_secured_endpoint_denied_for_anonymous(self):
        """5. Анонімного користувача не пускає на захищений ендпоінт замовлень."""
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Тести каталогу + фільтрації (7 тестів)
    def test_get_books_list(self):
        """6. Перегляд списку книг доступний усім анонімам."""
        response = self.client.get(self.books_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data) # перевірка пагінації

    def test_get_book_detail(self):
        """7. Перегляд детальної інформації про книгу."""
        response = self.client.get(f"{self.books_url}{self.book1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Dune')
        self.assertEqual(response.data['category_detail']['name'], 'Sci-Fi') # перевірка вкладеності

    def test_filter_books_by_category(self):
        """8. Фільтрація книг за ID категорії."""
        response = self.client.get(f"{self.books_url}?category={self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_books_by_price_range(self):
        """9. Фільтрація за діапазоном цін (gte/lte)."""
        response = self.client.get(f"{self.books_url}?price__gte=200")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Dune')

    def test_search_books(self):
        """10. Повнотекстовий пошук за назвою або автором."""
        response = self.client.get(f"{self.books_url}?search=Tolkien")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'Hobbit')

    def test_anonymous_cannot_create_book(self):
        """11. Анонім не може створити нову книгу."""
        data = {'title': 'New', 'author': 'A', 'price': 100, 'stock': 5, 'category': self.category.id}
        response = self.client.post(self.books_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_book(self):
        """12. Адміністратор з токеном має право створювати книгу."""
        self.client.force_authenticate(user=self.admin)
        data = {'title': 'New Book', 'author': 'Author', 'price': 150.00, 'stock': 5, 'category': self.category.id}
        response = self.client.post(self.books_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)

    # Тести кошика та замовлень
class CartAndOrderAPITestCase(APITestCase):
    def setUp(self):
        # Створення користувачів
        self.user1 = User.objects.create_user(username='buyer1', email='buyer1@test.com', password='password123')
        self.user2 = User.objects.create_user(username='buyer2', email='buyer2@test.com', password='password123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='password123')

        # Базові дані
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.book = Book.objects.create(
            title='1984', author='George Orwell', price=150.00, stock=5, category=self.category
        )

        # URL ендпоінти
        self.cart_url = '/api/v1/cart/'
        self.cart_add_url = '/api/v1/cart/add/'
        self.cart_remove_url = '/api/v1/cart/remove/'
        self.cart_clear_url = '/api/v1/cart/clear/'
        self.orders_url = '/api/v1/orders/'

    # Тести кошика сесій (6 тестів)
    def test_get_empty_cart(self):
        """13. Отримання порожнього кошика повертає успішний статус та порожній список."""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(float(response.data['total_cost']), 0.0)

    def test_add_item_ot_cart_success(self):
        """14. Успішне додавання книги до кошика."""
        data = {'book_id': self.book.id, 'quantity': 2}
        response = self.client.post(self.cart_add_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Перевірка вмісту кошика після додавання
        cart_res = self.client.get(self.cart_url)
        self.assertEqual(len(cart_res.data['items']), 1)
        self.assertEqual(cart_res.data['items'][0]['quantity'], 2)

    def test_add_item_to_cart_invalid_book_id(self):
        """15. Спроба додати неіснуючу книгу повертає помилку 400."""
        data = {'book_id': 9999, 'quantity': 1}
        response = self.client.post(self.cart_add_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_cart_quantity_override(self):
        """16. Оновлення кількості товару з прапорцем override_quantity."""
        # Додавання 1 книги
        self.client.post(self.cart_add_url, {'book_id': self.book.id, 'quantity': 1})

        # Перезаписування кількості книг на 3
        data = {'book_id': self.book.id, 'quantity': 3, 'override_quantity': True}
        response = self.client.post(self.cart_add_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cart_res = self.client.get(self.cart_url)
        self.assertEqual(cart_res.data['items'][0]['quantity'], 3)

    def test_remove_item_from_cart(self):
        """17. Успішне видалення книги з кошика повністю."""
        self.client.post(self.cart_add_url, {'book_id': self.book.id, 'quantity': 1})

        response = self.client.post(self.cart_remove_url, {'book_id': self.book.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cart_res = self.client.get(self.cart_url)
        self.assertEqual(len(cart_res.data['items']), 0)

    def test_clear_cart(self):
        """18. Повне очищення кошика."""
        self.client.post(self.cart_add_url, {'book_id': self.book.id, 'quantity': 2})

        response = self.client.post(self.cart_clear_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_res = self.client.get(self.cart_url)
        self.assertEqual(len(cart_res.data['items']), 0)

    # Тести замовлень та обмежень (7 тестів)
    def test_create_order_empty_cart_fails(self):
        """19. Спроба створити замовлення з порожнім кошиком повертає помилку 400."""
        self.client.force_authenticate(user=self.user1)
        data = {
            'first_name': 'Yevhen', 'last_name': 'Test', 'email': 'buyer1@test.com', 'address': 'Main St 1',
            'postal_code': '12345', 'city': 'Dnipro'
        }
        response = self.client.post(self.orders_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Ваш кошик порожній. Немає товарів для оформлення замовлення.')

    def test_create_order_success(self):
        """20. Успішне створення замовлення, списання залишку на складі та очищення кошика."""
        self.client.force_authenticate(user=self.user1)

        # Додавання книги в кошик
        cart_response = self.client.post(self.cart_add_url, {'book_id': self.book.id, 'quantity': 2})
        self.assertEqual(cart_response.status_code, status.HTTP_200_OK)

        # Примусова авторизація
        self.client.force_authenticate(user=self.user1)

        data = {
            'first_name': 'Yevhen', 'last_name': 'Test', 'email': 'buyer1@test.com', 'address': 'Main St 1',
            'postal_code': '12345', 'city': 'Dnipro'
        }
        response = self.client.post(self.orders_url, data)

        # Перевірка на створення замовлення
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Оновлення об'єкт книги з бд
        self.book.refresh_from_db()

        # Перевірка списання товару зі складу (було 5, придбали 2, залишилось 3)
        self.assertEqual(self.book.stock, 3)

        # Перевірка очищення кошика
        cart_res = self.client.get(self.cart_url)
        self.assertEqual(len(cart_res.data['items']), 0)

    def test_create_order_insufficient_stock(self):
        """21. Помилка при спробі купити більше книг, ніж є на складі."""
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.cart_add_url, {'book_id': self.book.id, 'quantity': 10})

        data = {
            'first_name': 'Yevhen', 'last_name': 'Test', 'email': 'buyer1@test.com', 'address': 'Main St 1',
            'postal_code': '12345', 'city': 'Dnipro'
        }
        response = self.client.post(self.orders_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Недостатньо товару '1984' на складі", response.data['error'])

    def test_user_can_only_see_their_own_orders(self):
        """22. Користувач бачить лише власні замовлення і не бачить замовлень інших користувачів."""
        # Створення замовлення для user1
        order_user1 = Order.objects.create(
            first_name='User1', last_name='L', email='buyer1@test.com',
            address='Addr 1', postal_code='11', city='C'
        )
        # А також замовлення для user2
        order_user2 = Order.objects.create(
            first_name='User2', last_name='L', email='buyer2@test.com',
            address='Addr 2', postal_code='22', city='C'
        )

        # Авторизація user1
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.orders_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Повинно повернутись лише 1 замовлення для buyer1@test.com
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['email'], 'buyer1@test.com')

    def test_admin_can_see_all_orders(self):
        """23. Адміністратор системи бачить замовлення всіх користувачів."""
        Order.objects.create(first_name='U1', last_name='L', email='buyer1@test.com', address='A', postal_code='1', city='C')
        Order.objects.create(first_name='U2', last_name='L', email='buyer2@test.com', address='A', postal_code='1', city='C')

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_order_detail_is_owner_permission(self):
        """24. Звичайний користувач не може переглянути деталі чужого замовлення за прямим ID."""
        order_user2 = Order.objects.create(
            first_name = 'User2', last_name='L', email='buyer2@test.com',
            address='Addr 2', postal_code='22', city='C'
        )

        # Логін як user1 + намагання отримати замовлення user2
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{self.orders_url}{order_user2.id}/")

        # Отримання 404 (через get_queryset, який не бачить це замовлення для user1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_creation_validation_errors(self):
        """25. Перевірка валідації полів замовлення (наприклад, некоректний email)."""
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.cart_add_url, {'book_id': self.book.id, 'quantity': 1})

        data = {
            'first_name': 'Yevhen', 'last_name': 'Test', 'email': 'not-an-email',
            'address': 'Main St 1', 'postal_code': '12345', 'city': 'Dnipro'
        }
        response = self.client.post(self.orders_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

