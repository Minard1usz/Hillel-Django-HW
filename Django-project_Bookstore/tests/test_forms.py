import pytest
from orders.forms import CartAddBookForm, OrderCreateForm

# тести для CartAddBookForm
# перевірка, чи форма валідна з коректними даними
def test_cart_add_book_form_valid_data():
    data = {'quantity': 5, 'override': False}
    form = CartAddBookForm(data=data)
    assert form.is_valid()
    assert form.cleaned_data['quantity'] == 5
    assert form.cleaned_data['override'] is False

# перевірка, що форма не пропустить кількість більше ніж 20
def test_cart_add_book_form_invalid_quantity():
    data = {'quantity': 25, 'override': False}
    form = CartAddBookForm(data=data)
    assert not form.is_valid()
    assert 'quantity' in form.errors

# перевірка на дефолтне значення override, якщо воно не вказане
def test_cart_add_book_form_default_values():
    data = {'quantity': 1}
    form = CartAddBookForm(data=data)
    assert form.is_valid()
    assert form.cleaned_data['override'] is False

# тести для OrderCreateForm
# перевірка валідації форми замовлення з коректними даними
def test_order_create_form_valid_data():
    data = {
        'first_name': 'Майк',
        'last_name': 'Вазовскі',
        'email': 'vazovski@example.com',
        'address': 'вул. Хрещатик, 1',
        'city': 'Київ',
        'postal_code': '01001'
    }
    form = OrderCreateForm(data=data)
    assert form.is_valid()

# перевірка, що форма невалідна, якщо пропускаються обов'язкові поля
def test_order_create_form_missing_required_fields():
    data = {
        'first_name': '',
        'last_name': 'Тестовий',
        'email': 'no-email',
        'address': '',
        'city': 'Kharkiv',
        'postal_code': '01001'
    }

    form = OrderCreateForm(data=data)
    assert not form.is_valid()
    assert 'first_name' in form.errors
    assert 'email' in form.errors
    assert 'address' in form.errors

# перевірка на граничне мінімальне значення кількості (1)
def test_cart_add_book_form_min_boundary():
    form = CartAddBookForm(data={'quantity': 1})
    assert form.is_valid()

# перевірка на граничне максимальне значення кількості (20)
def test_cart_add_book_form_max_boundary():
    form = CartAddBookForm(data={'quantity': 20})
    assert form.is_valid()
