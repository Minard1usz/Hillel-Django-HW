from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.conf import settings
from django.urls import reverse
import stripe
from decimal import ROUND_HALF_UP, Decimal
from django.views.decorators.http import require_POST, require_http_methods
from asgiref.sync import sync_to_async
from .cart import Cart
from .forms import CartAddBookForm, OrderCreateForm
from .models import OrderItem, Order
from shop_app.models import Book
from django.core.mail import send_mail
from .services import WarehouseService, WarehouseServiceError

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


@require_POST
def cart_add(request, book_id):
    """
    Синхронна view-функція для додавання книги до кошика або оновлення її кількості.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту, що містить POST-дані форми.
        book_id (int): Первинний ключ (ID) книги, яку потрібно додати.

    Returns:
        HttpResponseRedirect: Перенаправлення користувача на сторінку детального перегляду кошика.
    """
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    form = CartAddBookForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(book=book, quantity=cd["quantity"], override_quantity=cd["override"])
    return redirect("orders:cart_detail")


@require_POST
def cart_remove(request, book_id):
    """
    Синхронна view-функція для повного видалення книги з кошика сесії.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту.
        book_id (int): Первинний ключ (ID) книги, яку потрібно видалити.

    Returns:
        HttpResponseRedirect: Перенаправлення користувача на сторінку детального перегляду кошика.
    """
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect("orders:cart_detail")


async def cart_detail(request):
    """
    Асинхронна view-функція для відображення вмісту кошика користувача.

    Для безпечної роботи із синхронними сесіями Django (`request.session`)
    та кошиком логіка виділена у внутрішню ізольовану функцію `prepare_cart_data`,
    яка викликається асинхронним диспетчером через `sync_to_async`.
    Для кожного товару ініціалізується форма оновлення кількості.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту від користувача.

    Returns:
        HttpResponse: Зрендерена HTML-сторінка кошика з переданим списком товарів
        та формами для редагування кількості.
    """

    def prepare_cart_data():
        cart = Cart(request)
        cart_items = []

        for item in cart:
            item["update_quantity_form"] = CartAddBookForm(
                initial={"quantity": item["quantity"], "override": True}
            )
            cart_items.append(item)

        return cart, cart_items

    cart, cart_items = await sync_to_async(prepare_cart_data)()

    return render(
        request, "orders/cart_detail.html", {"cart": cart, "cart_items": cart_items}
    )


class InsufficientStockError(Exception):
    """Піднімається, коли на складі недостатньо товару під час checkout."""


def _handle_order_get(request):
    """
    Синхронна логіка для GET-запиту: безпечно ініціалізує форму та кошик.

    Викликається асинхронним диспетчером `order_create` через `sync_to_async`
    для ізоляції роботи із синхронною сесією Django (`Cart`).

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту від користувача.

    Returns:
        HttpResponse: Зрендерена HTML-сторінка з порожньою формою замовлення
        та вмістом кошика.
    """
    cart = Cart(request)
    form = OrderCreateForm()
    return render(
        request,
        "orders/order_create.html",
        {"cart": cart, "cart_items": list(cart), "form": form},
    )


def _handle_order_post(request):
    """
    Синхронна логіка для POST-запиту: обробка транзакції, створення замовлення
    та міжсервісне резервування товарів у ProjectB (Warehouse Service).
    """
    cart = Cart(request)
    cart_items = list(cart)

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

    form = OrderCreateForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "orders/order_create.html",
            {"cart": cart, "cart_items": cart_items, "form": form},
        )

    try:
        with transaction.atomic():
            # 1. Зберігаємо замовлення
            order = form.save()

            for item in cart_items:
                # Блокуємо рядок книги в БД від race conditions
                book = Book.objects.select_for_update().get(pk=item["book"].id)

                # Локальна перевірка наявності товару (1 етап)
                if book.stock < item["quantity"]:
                    raise InsufficientStockError(
                        f'Недостатньо товару "{book.title}" на складі '
                        f"(доступно: {book.stock})."
                    )

                # 2. Міжсервісний запит до ProjectB (Warehouse Service)
                # Якщо повертає помилку, raise підніме WarehouseServiceError
                # аби відкотити транзакцію в БД через transaction.atomic()
                WarehouseService.reserve_stock(
                    book_id=book.id,
                    quantity=item["quantity"],
                    order_id=order.id,
                )

                # 3. Створюємо елемент замовлення
                OrderItem.objects.create(
                    order=order,
                    book=book,
                    price=book.price,  # Ціна з БД
                    quantity=item["quantity"],
                )

                # 4. Списуємо залишок (локально)
                book.stock -= item["quantity"]
                book.save(update_fields=["stock"])

        # Очищуємо кошик та записуємо order_id в сесії
        cart.clear()
        request.session["order_id"] = order.id
        return redirect("orders:payment_process")

    except (InsufficientStockError, WarehouseServiceError) as exc:
        # Якщо є помилка резерву на складі чи нестачі товару
        return render(
            request,
            "orders/order_create.html",
            {"cart": cart, "cart_items": cart_items, "form": form, "error": f"Помилка створення замовлення: {exc}"},
        )
    except Book.DoesNotExist:
        return render(
            request,
            "orders/order_create.html",
            {
                "cart": cart,
                "cart_items": cart_items,
                "form": form,
                "error": "Один із товарів більше не доступний.",
            },
        )


@require_http_methods(["GET", "POST"])
async def order_create(request):
    """
    Асинхронний диспетчер для ініціалізації та обробки створення замовлення.

    Делегує роботу відповідним синхронним функціям-обробникам (`_handle_order_get`
    або `_handle_order_post`) через `sync_to_async`, щоб уникнути конфліктів
    асинхронного контексту із синхронними сесіями Django та ORM.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту від користувача.

    Returns:
        HttpResponse: Рендеринг сторінки оформлення замовлення (GET або POST з помилками)
        або редірект на сторінку ініціалізації оплати Stripe (успішний POST).
    """
    if request.method == "GET":
        return await sync_to_async(_handle_order_get)(request)

    return await sync_to_async(_handle_order_post)(request)


def _to_stripe_amount(price: Decimal) -> int:
    """
    Конвертує ціну типу Decimal у мінімальні одиниці валюти (копійки) для Stripe API.

    Використовує фінансове округлення `ROUND_HALF_UP` через метод `.quantize()`.
    Це запобігає класичним багам Python при роботі з типами з плаваючої крапкою
    (floating-point inaccuracies), гарантуючи точність фінансових транзакцій.

    Args:
        price (Decimal): Ціна товару або замовлення з копійками (наприклад, 199.90).

    Returns:
        int: Ціна в копійках, приведена до цілого числа (наприклад, 19990).
    """
    return int((price * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _build_line_items(order: Order) -> list[dict]:
    """
    Формує структуру line_items для передачі в Stripe Checkout Session.

    Оптимізує SQL-запити до бази даних за допомогою `select_related("book")`,
    що дозволяє уникнути проблеми N+1 при завантаженні назв книг для кожного елемента замовлення.

    Args:
        order (Order): Об'єкт замовлення, для якого формується платіжний чек.

    Returns:
        list[dict]: Список словників у форматі, який суворо вимагає Stripe API
        для опису товарних позицій (ціна, валюта в нижньому регістрі, назва, кількість).
    """
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
    """
        Синхронна view-функція для ініціалізації платіжної сесії у системі Stripe.

        Перевіряє наявність замовлення в сесії користувача та статус його оплати.
        При POST-запиті формує кошик товарів із захищеними цінами з БД, інтегрує
        idempotency_key для захисту від подвійних кліків та перенаправляє користувача
        на захищену сторінку оплати Stripe Checkout.

        Args:
            request (HttpRequest): Об'єкт HTTP-запиту від користувача.

        Returns:
            HttpResponse: Рендеринг сторінки підтвердження оплати (GET) або 
            тимчасовий редірект (HTTP 303 Redirect) на платіжну форму Stripe (POST).
        """
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


def payment_completed(request):
    """
    Синхронна view-функція для відображення сторінки успішної оплати замовлення.

    Сюди користувача перенаправляє Stripe після успішного списання коштів.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту.

    Returns:
        HttpResponse: HTML-сторінка з підтвердженням успішного оформлення замовлення.
    """
    order_id = request.session.get("order_id")
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        order.paid = True
        order.save()

        subject = f"Замовлення №{order.id} успішно оплачено!"
        message = (
            f"Вітаємо, {order.first_name}!\n\n"
            f"Дякуємо за покупку в нашому магазині Книгарня."
            f"Ваше замовлення №{order.id} успішно оплачено. \n"
            f"Сума до сплати: {order.get_total_cost()} грн. \n\n"
            f"Ми вже готуємо Ваші книги до відправки!"
        )

        send_mail(
            subject,
            message,
            "admin@bookstore.com",
            [order.email],
            fail_silently=False,
        )

    return render(request, "orders/created.html")


def payment_canceled(request):
    """
    Синхронна view-функція для відображення сторінки скасованої оплати.

    Сюди користувача перенаправляє Stripe, якщо він натиснув "Назад" або скасував сесію.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту.

    Returns:
        HttpResponse: HTML-сторінка з повідомленням про скасування транзакції.
    """
    return render(request, "orders/canceled.html")
