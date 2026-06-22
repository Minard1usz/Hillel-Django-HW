from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.conf import settings
from django.urls import reverse
import stripe
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import CartAddBookForm, OrderCreateForm
from .models import OrderItem, Order
from shop_app.models import Book
from django.core.mail import send_mail



stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


@require_POST
def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    form = CartAddBookForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            book=book,
            quantity=cd['quantity'],
            override_quantity=cd['override']
        )
    return redirect('orders:cart_detail')


@require_POST
def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('orders:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddBookForm(initial={
            'quantity': item['quantity'],
            'override': True
        })
    return render(request, 'orders/cart_detail.html', {'cart': cart})


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save()

                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        book=item['book'],
                        price=item['price'],
                        quantity=item['quantity']
                    )

                cart.clear()

            request.session['order_id'] = order.id

            return redirect('orders:payment_process')
    else:
        form = OrderCreateForm()

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


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


def payment_completed(request):
    order_id = request.session.get('order_id')
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
            'admin@bookstore.com',
            [order.email],
            fail_silently=False,
        )

    return render(request, 'orders/created.html')


def payment_canceled(request):
    return render(request, 'orders/canceled.html')


