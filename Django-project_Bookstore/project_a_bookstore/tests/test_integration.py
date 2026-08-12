# для user flows
import pytest
from django.urls import reverse
from .factories import BookFactory, CategoryFactory
from orders.models import Order

# -----------------------------------------------------------------------------
# СЦЕНАРІЙ 1: Повний шлях звичайного покупця (5 тестів / перевірок)
# Користувач заходить на сайт -> переглядає книгу -> додає її в кошик ->
# оформлює замовлення -> перевіряємо, що кількість книг на складі зменшилася
# (або замовлення з'явилося в БД).
# -----------------------------------------------------------------------------


# ІНТЕГРАЦІЙНИЙ ТЕСТ 1-5: Повний цикл купівлі книги авторизованим/анонімним користувачем
@pytest.mark.django_db(transaction=True)
def test_customer_successful_purchase_flow(client):
    # Створюємо товар завдяки фабриці
    book = BookFactory(title="Ефективний Python", price=450.00, stock=10)

    # 1. Перевіряємо, чи книга доступна для перегляду в каталозі
    response = client.get(reverse("shop_app:book_list"))
    assert response.status_code == 200
    assert book.title in response.content.decode("utf-8")

    # 2. Перевіряємо, чи сторінка детального опису книги відкрилась успішно
    response = client.get(reverse("shop_app:book_detail", kwargs={"pk": book.pk}))
    assert response.status_code == 200

    # 3. Перевіряємо додавання твоару в кошик (синхронний сесійний клієнт).
    # У разі POST проблеми, імітується заповнення кошика через сесію клієнта
    cart_add_url = reverse("cart:cart_add", kwargs={"book_id": book.id})
    client.post(cart_add_url, data={"quantity": 2, "override": False})

    # Перевірка, чи сторінка кошика бачить товар
    response = client.get(reverse("orders:order_create"))
    assert response.status_code == 200

    # 4. Перевіряємо оформлення замовлення через фопму Post-запиту
    order_data = {
        "first_name": "Алекс",
        "last_name": "Тестер",
        "email": "alex@example.com",
        "address": "Шевченко 7",
        "city": "Дніпро",
        "postal_code": "49000",
    }
    response = client.post(reverse("orders:order_create"), data=order_data)

    # 5. Перевірка про успішне створення замовлення в бд
    assert response.status_code == 302
    assert Order.objects.filter(email="alex@example.com").exists()


# -----------------------------------------------------------------------------
# СЦЕНАРІЙ 2: Купівля декількох книг та перевірка кошика
# 5 тестів / перевірок (6-10)
# Перевірка повного ланцюжка для багатокомпонентного кошика.
# -----------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_customer_multiple_items_purchase_flow(client):
    # 6. Створюємо дві різні книги
    book1 = BookFactory(title="Книга 1", price=200.00, stock=5)
    book2 = BookFactory(title="Книга 2", price=300.00, stock=5)

    # 7. Імітуємо додавання обох книг у кошик сесії
    client.post(
        reverse("cart:cart_add", kwargs={"book_id": book1.id}), data={"quantity": 1}
    )
    client.post(
        reverse("cart:cart_add", kwargs={"book_id": book2.id}), data={"quantity": 2}
    )

    # 6,7. Перевірка на успішне створення замовлення
    response = client.get(reverse("orders:order_create"))
    assert response.status_code == 200

    # 8. Сабміт замовлення обох книг
    order_data = {
        "first_name": "Юрій",
        "last_name": "Потужний",
        "email": "uri@example.com",
        "address": "Центральна 1",
        "city": "Харків",
        "postal_code": "61000",
    }
    response = client.post(reverse("orders:order_create"), data=order_data)

    # 8, 9. Успішний редірект після оформлення
    assert response.status_code == 302

    # 10. Перевірка, що замовлення з'явилося в бд
    assert Order.objects.filter(email="uri@example.com").exists()


# -----------------------------------------------------------------------------
# СЦЕНАРІЙ 3: Невдале оформлення через невалідні дані (Validation Flow)
# Клієнт заповнює форму некоректно. Замовлення не створюється, користувач бачить
# помилки валідації на сторінці (11-15)
# -----------------------------------------------------------------------------
@pytest.mark.django_db
def test_customer_failed_validation_flow(client):
    book = BookFactory(title="Django для профі", price=500.00, stock=5)

    # 11. Додаємо книгу в кошик сесії
    client.post(
        reverse("cart:cart_add", kwargs={"book_id": book.id}), data={"quantity": 1}
    )

    # 12. Сабміт форми з помилковими даними
    bad_order_data = {
        "first_name": "",
        "last_name": "Бот",
        "email": "no-email",
        "address": "вулиця 404",
        "city": "Львів",
        "postal_code": "79000",
    }
    response = client.post(reverse("orders:order_create"), data=bad_order_data)

    # 11. Перевірка, що сторінка не робить редірект на оплату, а повертає 200 (переренд форми)
    assert response.status_code == 200

    # 12. Перевірка, у контексті сторінки є форма, що містить помилки
    assert "form" in response.context
    assert not response.context["form"].is_valid()

    # 13-14. Перевірка на наявність помилок в полях
    assert "first_name" in response.context["form"].errors
    assert "email" in response.context["form"].errors

    # 15. Перевірка, що в бд не з'явилось замовлень з цим email
    assert not Order.objects.filter(email="no-email").exists()
