from sqlite3 import IntegrityError

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from shop_app.models import Category, Book


@pytest.mark.django_db
def test_category_model_str():
    # Generated with AI, reviewed and modified
    category = Category.objects.create(name="Фантастика", slug="fantastic")
    assert str(category) == "Фантастика"


@pytest.mark.django_db
def test_category_meta_verbose_name():
    # Generated with AI, reviewed and modified
    assert str(Category._meta.verbose_name) == "Категорія"
    assert str(Category._meta.verbose_name_plural) == "Категорії"


@pytest.mark.django_db
def test_book_model_str():
    # Generated with AI, reviewed and modified
    category = Category.objects.create(name="Детектив", slug="detective")
    book = Book.objects.create(
        title="Шерлок Холмс",
        author="Артур Конан Дойл",
        price=Decimal("250.00"),
        stock=10,
        category=category,
    )
    assert str(book) == "Шерлок Холмс by Артур Конан Дойл"


@pytest.mark.django_db
def test_book_default_stock():
    # Generated with AI, reviewed and modified
    category = Category.objects.create(name="Наука", slug="science")
    book = Book.objects.create(
        title="Короткі відповіді на великі питання",
        author="Стівен Гокінг",
        price=Decimal("320.00"),
        category=category,
    )
    assert book.stock == 0


@pytest.mark.django_db(transaction=True)
def test_book_negative_stock_validation():
    # Generated with AI, reviewed and modified
    category = Category.objects.create(name="Хобі", slug="hobby")
    book = Book(
        title="Тест",
        author="Тестовий Автор",
        price=Decimal("10.00"),
        stock=-5,
        category=category,
    )
    with pytest.raises(ValidationError):
        book.full_clean()


from django.core.exceptions import ValidationError
from decimal import Decimal
import pytest


@pytest.mark.django_db
def test_book_blank_title_validation():
    # Generated with AI, reviewed and modified
    category = Category.objects.create(name="Хобі", slug="hobby")

    book = Book(
        title="",
        author="Тестовий Автор",
        price=Decimal("10.00"),
        stock=5,
        category=category,
    )

    with pytest.raises(ValidationError):
        book.full_clean()
