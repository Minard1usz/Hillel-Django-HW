import factory
import pytest
from .factories import CategoryFactory, BookFactory


# перевірка, чи правильно форма створюється через фабрику
@pytest.mark.django_db
def test_category_creation():
    category = CategoryFactory(name="Фантастика", slug="fantastic")

    assert category.id is not None
    assert category.name == "Фантастика"
    assert category.slug == "fantastic"


# перевірка на рядкове представлення моделі Category
@pytest.mark.django_db
def test_category_str_method():
    category = CategoryFactory(name="Детективи")

    assert str(category) == "Детективи"


# перевірка на автоматичне створення книг та категорії
@pytest.mark.django_db
def test_book_creation_with_subfactory():
    book = BookFactory(title="Гаррі Поттер", author="Дж. Роулінг", price=350.00)

    assert book.id is not None
    assert book.title == "Гаррі Поттер"
    assert book.author == "Дж. Роулінг"
    assert book.price == 350.00
    assert book.category.id is not None


# перевірка на рядкове представлення моделі Book
@pytest.mark.django_db
def test_book_str_method():
    book = BookFactory(title="Кобзар", author="Тарас Шевченко")

    assert str(book) == "Кобзар by Тарас Шевченко"


# перевірка, що за замовчуванням кількість книг на складі дорівнює 0
@pytest.mark.django_db
def test_book_default_stock():
    from shop_app.models import Book

    category = CategoryFactory()

    new_book = Book.objects.create(
        title="Тест Сток",
        author="Автор",
        price=100.00,
        category=category,
    )
    assert new_book.stock == 0


# перевірка, що працює related_name='books' з категорії до книг
@pytest.mark.django_db
def test_category_related_name():
    category = CategoryFactory()
    BookFactory.create_batch(2, category=category)

    assert category.books.count() == 2
