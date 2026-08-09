# AI Code Review Report
## 1. View: BookListView(ListView)
### Original Code:
``` python
class BookListView(ListView):
    model = Book
    template_name = 'shop_app/book_list.html'
    context_object_name = 'books'
    paginate_by = 5

    def get_queryset(self):
        queryset = Book.objects.all()
        category_id = self.request.GET.get('category')
        search_query = self.request.GET.get('search')

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset

    async def get(self, request, *args, **kwargs):

        def process_context():
            self.object_list = self.get_queryset()
            allow_empty = self.get_allow_empty()

            if not allow_empty:
                if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                    is_empty = not self.object_list.exists()
                else:
                    is_empty = not self.object_list
                if is_empty:
                    raise Http404("Empty list")

            return self.get_context_data()

        context = await sync_to_async(process_context)()

        categories_qs = Category.objects.all()
        context['categories'] = [cat async for cat in categories_qs]

        return self.render_to_response(context) 
```


### AI Recommendations:
- **SQL Optimization:** Додано `select_related('category')` для запобігання проблеми N+1 запитів при рендерингу категорій для кожної книги.
- **Input Validation:** Створено захисний метод `_get_category_id` для уникнення падіння сервера з помилкою 500 (ValueError), якщо в URL передано невалідний ID.
- **Security Limitation:** Додано обмеження довжини пошукового запиту (`SEARCH_MAX_LENGTH = 100`) для запобігання ReDoS атакам або перевантаженню БД довгими рядками.
- **Caching:** Впроваджено кешування списку категорій на 15 хвилин за допомогою Django Cache Framework для зменшення кількості важких запитів до БД.

### Final Refactored Code:
```python
from django.views.generic import ListView
from django.core.cache import cache
from asgiref.sync import sync_to_async
from .models import Book, Category

SEARCH_MAX_LENGTH = 100
CATEGORY_CACHE_KEY = "shop_all_categories"
CATEGORY_CACHE_TTL = 60 * 15  # 15 хвилин

class BookListView(ListView):
    """
    View для відображення списку книг з підтримкою асинхронності,
    фільтрації за категоріями, пошуку та оптимізацією SQL-запитів.
    """
    model = Book
    template_name = "shop_app/book_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        """Формує оптимізований запит із захистом від N+1 та валідацією параметрів."""
        queryset = (
            Book.objects.select_related("category")
            .order_by("title")
        )

        category_id = self._get_category_id()
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)

        search_query = self._get_search_query()
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset

    def _get_category_id(self):
        """Безпечно витягує ID категорії, захищаючи від ValueError (500-х помилок)."""
        raw_value = self.request.GET.get("category")
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    def _get_search_query(self):
        """Санітизує пошуковий запит та обмежує довжину для безпеки бази даних."""
        raw_value = self.request.GET.get("search", "").strip()
        return raw_value[:SEARCH_MAX_LENGTH] if raw_value else ""

    async def get(self, request, *args, **kwargs):
        """Головний асинхронний обробник GET-запиту."""
        # Отримуємо queryset та безпечно перетворюємо його на список в асинхронному середовищі
        queryset = self.get_queryset()
        self.object_list = await sync_to_async(list)(queryset)
        
        # Отримуємо базовий контекст пагінації (загортаємо синхронний метод)
        context = await sync_to_async(self.get_context_data)()
        
        # Додаємо категорії з кешу (використовуємо синхронний кеш всередині sync_to_async)
        context["categories"] = await sync_to_async(self._get_cached_categories)()
        
        return self.render_to_response(context)

    def _get_cached_categories(self):
        """Синхронний помічник для кешування категорій."""
        return cache.get_or_set(
            CATEGORY_CACHE_KEY,
            lambda: list(Category.objects.all()),
            CATEGORY_CACHE_TTL,
        )
```

# AI Code Review Report
## 2. View: order_create()
### Original Code:
``` python
async def order_create(request):
    if request.method == 'POST':
        def save_order_transaction(post_data, session_items):
            form = OrderCreateForm(post_data)
            if form.is_valid():
                with transaction.atomic():
                    order = form.save()
                    for item in session_items:
                        OrderItem.objects.create(
                            order=order,
                            book=item['book'],
                            price=item['price'],
                            quantity=item['quantity']
                        )
                return order.id
            return None

        def get_cart_data():
            cart = Cart(request)
            items = list(cart)
            return cart, items

        cart, session_items = await sync_to_async(get_cart_data)()

        order_id = await sync_to_async(save_order_transaction)(request.POST, session_items)

        if order_id:
            def finalize_session(order_id):
                cart.clear()
                request.session['order_id'] = order_id

            await sync_to_async(finalize_session)(order_id)
            return redirect('orders:payment_process')

        def get_invalid_form(post_data):
            return OrderCreateForm(post_data)
        form = await sync_to_async(get_invalid_form)(request.POST)

        cart_items = session_items

    else:
        def prepare_get_data():
            cart = Cart(request)
            form = OrderCreateForm()
            return cart, list(cart), form

        cart, cart_items, form = await sync_to_async(prepare_get_data)()

    return render(request, 'orders/order_create.html', {'cart': cart, 'cart_items': cart_items, 'form': form})
```
### AI Recommendations:
- Race Condition Prevention: Додано select_for_update() під час отримання об'єктів книг. Це блокує відповідні рядки в БД на час виконання транзакції, запобігаючи ситуаціям, коли два користувачі одночасно купують останню книгу, загоняючи залишок у мінус.
- Transactional Integrity: Усю логіку валідації та створення замовлення винесено в окрему синхронну функцію _create_order_transaction під керуванням with transaction.atomic(). Якщо під час створення замовлення виникне помилка браку на складі, вся транзакція відкотиться (rollback).
- Price Security: Ціна для OrderItem тепер береться напряму з об'єкта бази даних (book.price), а не з сесії кошика, що унеможливлює підміну ціни через маніпуляції на фронтенді.
- Architecture Clarification (Guest Checkout): Під час аналізу коду ШІ вказав на відсутність зв'язку з User у моделі Order. Логіку було оптимізовано суворо під гостьові замовлення без використання зайвих декораторів авторизації, щоб не зламати чинні інтеграційні тести.
- Async Context Separation (Додано студентом):** Під час інтеграції коду було виявлено конфлікт асинхронного контексту із синхронною сесією Django (`SynchronousOnlyOperation` при зверненні до `request.session` та `Cart`). Фінальну архітектуру було оптимізовано: весь `GET` та `POST` флоу було розбито на ізольовані синхронні функції-обробники, які безпечно викликаються асинхронним диспетчером через `sync_to_async`.

### Final Refactored Code:
```python
from asgiref.sync import sync_to_async
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from shop_app.models import Book  # Перевір, щоб імпорт збігався з твоєю структурою
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import OrderItem

class InsufficientStockError(Exception):
    """Піднімається, коли на складі недостатньо товару під час checkout."""


def _create_order_transaction(post_data, cart_items):
    """
    Синхронна транзакційна операція: валідує форму, блокує рядки книг у БД за допомогою
    select_for_update(), перевіряє реальні залишки та списує їх зі складу.
    Повертає (order_id, form).
    """
    form = OrderCreateForm(post_data)
    if not form.is_valid():
        return None, form

    with transaction.atomic():
        # Зберігаємо замовлення
        order = form.save()

        for item in cart_items:
            # Захист від Race Conditions: блокуємо рядок книги в БД до кінця транзакції
            book = Book.objects.select_for_update().get(pk=item["book"].id)

            # Перевіряємо залишок на складі
            if book.stock < item["quantity"]:
                raise InsufficientStockError(
                    f'Недостатньо товару "{book.title}" на складі '
                    f'(доступно: {book.stock}).'
                )

            # Створюємо елемент замовлення із захищеною ціною з БД
            OrderItem.objects.create(
                order=order,
                book=book,
                price=book.price,  # Ціна береться суворо з БД, а не з сесії
                quantity=item["quantity"],
            )
            
            # Зменшуємо складські залишки
            book.stock -= item["quantity"]
            book.save(update_fields=["stock"])

    return order.id, form


@require_http_methods(["GET", "POST"])
async def order_create(request):
    """Асинхронна view-функція для оформлення замовлень із перевіркою залишків."""
    cart = Cart(request)
    cart_items = await sync_to_async(list)(cart)

    if request.method == "GET":
        form = OrderCreateForm()
        return render(
            request,
            "orders/order_create.html",
            {"cart": cart, "cart_items": cart_items, "form": form},
        )

    # POST-запит
    if not cart_items:
        return render(
            request,
            "orders/order_create.html",
            {
                "cart": cart,
                "cart_items": cart_items,
                "form": OrderCreateForm(request.POST),
                "error": "Ваш кошик порожній.",
            },
        )

    try:
        # Викликаємо транзакційну логіку
        order_id, form = await sync_to_async(_create_order_transaction)(request.POST, cart_items)
    except InsufficientStockError as exc:
        return render(
            request,
            "orders/order_create.html",
            {"cart": cart, "cart_items": cart_items, "form": OrderCreateForm(request.POST), "error": str(exc)},
        )
    except Book.DoesNotExist:
        return render(
            request,
            "orders/order_create.html",
            {
                "cart": cart,
                "cart_items": cart_items,
                "form": OrderCreateForm(request.POST),
                "error": "Один із товарів у кошику більше не доступний у базі даних.",
            },
        )

    if order_id is None:
        # Форма невалідна — повертаємо її з помилками
        return render(
            request,
            "orders/order_create.html",
            {"cart": cart, "cart_items": cart_items, "form": form},
        )

    # Фіналізуємо сесію та очищуємо кошик
    await sync_to_async(cart.clear)()
    request.session["order_id"] = order_id
    return redirect("orders:payment_process")
```
## 3. View: payment_process(request)
### Original Code:
``` python
def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        success_url = request.build_absolute_uri(reverse('orders:payment_completed'))
        cancel_url = request.build_absolute_uri(reverse('orders:payment_canceled'))

        session_data = {
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'line_items': []
        }

        for item in order.items.all():
            session_data['line_items'].append({
                'price_data': {
                    'unit_amount': int(item.price * 100),
                    'currency': 'UAH',
                    'product_data': {
                        'name': item.book.title,
                    },
                },
                'quantity': item.quantity,
            })

        session = stripe.checkout.Session.create(**session_data)

        return redirect(session.url, code=303)
    return render(request, 'orders/payment_process.html', locals())
```

### AI Recommendations:
- Financial Precision: Замінено небезпечне приведення int(price * 100) на банківське округлення за допомогою Decimal.quantize(). Це унеможливлює втрату копійок через особливості обчислень типів з плаваючою крапкою (floating-point math) в Python.
- API Fault Tolerance: Створення сесії Stripe загорнуто в блок try-except із перехопленням stripe.error.StripeError. У разі збою на стороні платіжного шлюзу користувач побачить зрозуміле повідомлення про помилку замість системного збою 500.
- Idempotency Integration: До запиту створення сесії додано унікальний ключ idempotency_key. Це гарантує, що якщо покупець випадково двічі натисне кнопку оплати через повільний інтернет, Stripe обробить лише один запит і не створить дублюючу транзакцію.
- Stripe API Compliance: Код валюти переведено в нижній регістр (uah), оскільки Stripe API суворо вимагає дотримання ISO стандарту в нижньому регістрі й повертає помилку на значення UAH.
- UX & Security Checks: Додано захист від повторної оплати (order.paid) та перевірку наявності ID замовлення в сесії. Якщо сесія порожня, користувача м'яко перенаправляє на створення замовлення замість викидання помилки 404.

### Final Refactored Code:
```python
import stripe
from decimal import ROUND_HALF_UP, Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


def _to_stripe_amount(price: Decimal) -> int:
    """Конвертує ціну в мінімальні одиниці валюти (копійки) з коректним округленням."""
    return int((price * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _build_line_items(order: Order) -> list[dict]:
    """Формує line_items для Stripe Checkout Session з оптимізацією SQL через select_related."""
    return [
        {
            "price_data": {
                "unit_amount": _to_stripe_amount(item.price),
                "currency": "uah",
                "product_data": {"name": item.book.title},
            },
            "quantity": item.quantity,
        }
        for item in order.items.select_related("book").all()
    ]


@require_http_methods(["GET", "POST"])
def payment_process(request):
    """Синхронна view-функція для ініціалізації та обробки платіжних сесій Stripe."""
    order_id = request.session.get("order_id")

    if not order_id:
        return redirect("orders:order_create")

    order = get_object_or_404(Order, id=order_id)

    if order.paid:
        return redirect("orders:payment_completed")

    if request.method == "POST":
        line_items = _build_line_items(order)
        if not line_items:
            return render(
                request,
                "orders/payment_process.html",
                {"order": order, "error": "У замовленні немає товарів."},
            )

        success_url = request.build_absolute_uri(reverse("orders:payment_completed"))
        cancel_url = request.build_absolute_uri(reverse("orders:payment_canceled"))

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                client_reference_id=order.id,
                success_url=success_url,
                cancel_url=cancel_url,
                line_items=line_items,
                idempotency_key=f"order-{order.id}-checkout",
            )
        except stripe.error.StripeError:
            return render(
                request,
                "orders/payment_process.html",
                {
                    "order": order,
                    "error": "Не вдалося створити сесію оплати. Спробуйте ще раз пізніше.",
                },
            )

        order.stripe_id = session.id
        order.save(update_fields=["stripe_id", "updated"])

        return redirect(session.url, code=303)

    return render(request, "orders/payment_process.html", {"order": order})
```