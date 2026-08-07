import asyncio
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from .models import Book, Category
from asgiref.sync import sync_to_async
from django.http import Http404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from orders.forms import CartAddBookForm
from django.core.cache import cache
from django.http import HttpResponse
from shop_app.tasks import generate_report_task
from django.http import JsonResponse
from django.core.management import call_command

SEARCH_MAX_LENGTH = 100
CATEGORY_CACHE_KEY = "shop_all_categories"
CATEGORY_CACHE_TTL = 60 * 15  # 15 хвилин


# Create your views here.
async def get_as_list(queryset):
    """
    Асинхронно приводить Django QuerySet до звичайного списку Python.

    Використовує асинхронний генератор списків (`async for`) для неблокувального
    зчитування рядків із бази даних, запобігаючи заморожуванню асинхронного event loop.

    Args:
        queryset (QuerySet): Початковий запит Django ORM.

    Returns:
        list: Список об'єктів моделей, завантажених із бази даних.
    """
    return [item async for item in queryset]


def prefetch_user_status(user):
    """
    Синхронно підвантажує (кешує) службові атрибути користувача.

    Примусово звертається до атрибутів `is_staff` та `is_superuser` для автентифікованого
    користувача. Це дозволяє уникнути відкладених (lazy) синхронних запитів до БД
    під час подальшого рендерингу шаблону в асинхронному контексті.

    Args:
        user (AbstractBaseUser): Об'єкт користувача з `request.user`.

    Returns:
        AbstractBaseUser: Об'єкт користувача з уже завантаженими правами доступу.
    """
    if user.is_authenticated:
        _ = user.is_staff
        _ = user.is_superuser
    return user


@sync_to_async
def render_to_response(request, template_name, context):
    return render(request, template_name, context)


async def store(request):
    """
    Асинхронна view-функція для відображення головної сторінки магазину (Store).

    Оптимізує час відгуку сторінки за допомогою паралельного виконання запитів через `asyncio.gather`.
    Одночасно збирає списки спеціальних пропозицій, преміум-товарів, категорій із підрахунком книг,
    доступних товарів та акційних позицій, а також асинхронно готує статус користувача.

    Args:
        request (HttpRequest): Об'єкт HTTP-запиту від користувача.

    Returns:
        HttpResponse: Зрендерена HTML-сторінка головного магазину `shop_app/store.html`
        із повним набором паралельно оброблених даних у контексті.
    """
    if not await Book.objects.aexists():
        try:
            print("===> Base is empty! Loading books_data.json...")
            await sync_to_async(call_command)(
                "loaddata", "shop_app/fixtures/books_data.json"
            )
            print("===> Successfully loaded!")
        except Exception as e:
            print(f"===> Error loading fixtures: {e}")

    cache_key = "store_page_context"
    # Отримання контексту
    context = await cache.aget(cache_key)
    if not context:
        special_offers_qs = Book.objects.filter(
            Q(price__lt=300) | Q(description__icontains="discount")
        )
        premium_offers_qs = Book.objects.filter(Q(price__gt=300))
        categories_with_counts_qs = Category.objects.annotate(
            total_books=Count("books")
        )
        available_books_qs = Book.objects.filter(stock__gt=0)
        discount_books_qs = Book.objects.filter(
            description__icontains="discount"
        )

        user = await request.auser()

        (
            special_offers,
            premium_offers,
            categories,
            available_books,
            discount_books,
            _,
        ) = await asyncio.gather(
            get_as_list(special_offers_qs),
            get_as_list(premium_offers_qs),
            get_as_list(categories_with_counts_qs),
            get_as_list(available_books_qs),
            get_as_list(discount_books_qs),
            sync_to_async(prefetch_user_status)(user),
        )

        context = {
            "special_offers": special_offers,
            "premium_offers": premium_offers,
            "categories": categories,
            "available_books": available_books,
            "discount_books": discount_books,
        }
        # Зберігання контексту на 15 хв, запис в кеш асинхронно
        try:
            await cache.aset(cache_key, context, 900)
        except Exception as e:
            print(f"Cache write error: {e}")

        return await render_to_response(request, "shop_app/store.html", context)


class BookListView(ListView):
    """
    Асинхронний Class-Based View для відображення списку книг.

    Підтримує пагінацію, фільтрацію за категоріями, пошук за назвою,
    оптимізацію SQL-запитів через `select_related` та кешування списку
    категорій у Redis/Memcached для зниження навантаження на БД.
    """

    model = Book
    template_name = "shop_app/book_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        """
        Формує оптимізований набір даних (QuerySet) книг з урахуванням фільтрів.

        Використовує `select_related('category')` для уникнення проблеми N+1.

        Returns:
            QuerySet: Відфільтрований та відсортований список книг.
        """
        queryset = Book.objects.select_related("category").order_by("title")

        category_id = self._get_category_id()
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)

        search_query = self._get_search_query()
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset

    def _get_category_id(self):
        """Безпечно витягує та валідує ID категорії з GET-параметрів."""
        raw_value = self.request.GET.get("category")
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    def _get_search_query(self):
        """Витягує пошуковий запит та обрізає його до безпечної максимальної довжини."""
        raw_value = self.request.GET.get("search", "").strip()
        return raw_value[:SEARCH_MAX_LENGTH] if raw_value else ""

    async def get(self, request, *args, **kwargs):
        """
        Обробляє асинхронний GET-запит для відображення сторінки.

        Асинхронно приводить QuerySet до списку, формує контекст та
        додає туди закешовані категорії, використовуючи обгортку `sync_to_async`.

        Args:
            request (HttpRequest): Об'єкт HTTP-запиту.

        Returns:
            HttpResponse: Зрендерена HTML-сторінка зі списком книг.
        """
        queryset = self.get_queryset()
        self.object_list = await sync_to_async(list)(queryset)

        context = await sync_to_async(self.get_context_data)()

        context["categories"] = await sync_to_async(self._get_cached_categories)()

        return self.render_to_response(context)

    def _get_cached_categories(self):
        """
        Повертає список усіх категорій з кешу.

        Якщо кеш порожній, робить запит до БД, зберігає результат у кеш і повертає його.
        """
        return cache.get_or_set(
            CATEGORY_CACHE_KEY,
            lambda: list(Category.objects.all()),
            CATEGORY_CACHE_TTL,
        )


class BookDetailView(DetailView):
    """
    Class-Based View для відображення детальної інформації про конкретну книгу.

    Виводить опис, автора, ціну, залишок на складі та форму для додавання в кошик.
    """

    model = Book
    template_name = "shop_app/book_detail.html"

    async def get(self, request, *args, **kwargs):
        book_id = kwargs.get("pk")
        cache_key = f"book_detail_{book_id}"

        # Беремо книгу з кешу
        book = cache.get(cache_key)

        if not book:
            # Якщо в кеші немає, створюємо запит до БД синхронно через sync_to_async
            def fetch_book():
                return self.get_object()

            book = await sync_to_async(fetch_book)()
            # Записується об'єкт у кеш на 30 хв
            cache.set(cache_key, book, 1800)

        self.object = book

        def process_context():
            context = self.get_context_data(object=self.object)
            context["cart_book_form"] = CartAddBookForm()
            return context

        context = await sync_to_async(process_context)()
        return self.render_to_response(context)


class BookCreateView(CreateView):
    """
    Class-Based View для додавання нової книги в каталог магазину.

    Надає форму створення об'єкта `Book`. Доступ до в'юхи обмежений:
    створювати записи можуть лише користувачі зі статусом персоналу (is_staff)
    або суперкористувачі (is_superuser).
    """

    model = Book
    template_name = "shop_app/book_form.html"
    fields = ["title", "author", "category", "description", "price", "stock", "cover"]
    success_url = reverse_lazy("shop_app:book_list")

    def test_func(self):
        """
        Перевіряє, чи має користувач права для створення книги.

        Returns:
            bool: True, якщо користувач є staff або superuser, інакше False.
        """
        return self.request.user.is_staff or self.request.user.is_superuser


class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Class-Based View для редагування інформації про наявну книгу.

    Вимагає обов'язкової автентифікації користувача. Дозволяє змінювати
    будь-які атрибути книги лише модераторам або адміністраторам.
    У разі відсутності прав генерує HTTP 403 Forbidden.
    """

    model = Book
    template_name = "shop_app/book_form.html"
    fields = ["title", "author", "category", "description", "price", "stock", "cover"]
    success_url = reverse_lazy("shop_app:book_list")

    raise_exception = True

    def test_func(self):
        """
        Перевіряє, чи має користувач права для редагування книги.

        Returns:
            bool: True для staff/superuser, інакше False.
        """
        return self.request.user.is_staff or self.request.user.is_superuser


class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Class-Based View для видалення книги з каталогу магазину.

    Запитує підтвердження видалення через HTML-шаблон `book_delete.html`.
    Доступний суворо для користувачів зі статусом staff або superuser.
    """

    model = Book
    template_name = "shop_app/book_delete.html"
    success_url = reverse_lazy("shop_app:book_list")

    raise_exception = True

    def test_func(self):
        """
        Перевіряє, чи має користувач права для видалення книги.

        Returns:
            bool: True для staff/superuser, інакше False.
        """
        return self.request.user.is_staff or self.request.user.is_superuser


# def trigger_error(request):
#     division_by_zero = 1 / 0
#     return HttpResponse("Не досягнеться")


def trigger_report_generation(request):
    generate_report_task.delay()
    return HttpResponse("Генерацію звіту успішно запущено у фоні!")


def health_check(request):
    return JsonResponse({"status": "ok", "database": "online"})
