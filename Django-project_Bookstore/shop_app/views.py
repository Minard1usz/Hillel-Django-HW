import asyncio
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from .models import Book, Category
from asgiref.sync import sync_to_async
from django.http import Http404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from orders.forms import CartAddBookForm
from django.core.cache import cache


SEARCH_MAX_LENGTH = 100
CATEGORY_CACHE_KEY = "shop_all_categories"
CATEGORY_CACHE_TTL = 60 * 15  # 15 хвилин

# Create your views here.
async def get_as_list(queryset):
    return [item async for item in queryset]

def prefetch_user_status(user):
    if user.is_authenticated:
        _ = user.is_staff
        _ = user.is_superuser
    return user

async def store(request):
    special_offers_qs = Book.objects.filter(Q(price__lt=300) | Q(description__icontains='discount'))
    premium_offers_qs = Book.objects.filter(Q(price__gt=300))
    categories_with_counts_qs = Category.objects.annotate(total_books=Count('books'))
    available_books_qs = Book.objects.filter(stock__gt=0)
    discount_books_qs = Book.objects.filter(description__icontains='discount')

    special_offers, premium_offers, categories, available_books, discount_books, _ = await asyncio.gather(
        get_as_list(special_offers_qs),
        get_as_list(premium_offers_qs),
        get_as_list(categories_with_counts_qs),
        get_as_list(available_books_qs),
        get_as_list(discount_books_qs),
        sync_to_async(prefetch_user_status)(request.user)
    )

    context = {
        'special_offers': special_offers,
        'premium_offers': premium_offers,
        'categories': categories,
        'available_books': available_books,
        'discount_books': discount_books,
    }

    return render(request, 'shop_app/store.html', context)


class BookListView(ListView):
    model = Book
    template_name = "shop_app/book_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
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
        raw_value = self.request.GET.get("category")
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    def _get_search_query(self):
        raw_value = self.request.GET.get("search", "").strip()
        return raw_value[:SEARCH_MAX_LENGTH] if raw_value else ""

    async def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        self.object_list = await sync_to_async(list)(queryset)

        context = await sync_to_async(self.get_context_data)()

        context["categories"] = await sync_to_async(self._get_cached_categories)()

        return self.render_to_response(context)

    def _get_cached_categories(self):
        return cache.get_or_set(
            CATEGORY_CACHE_KEY,
            lambda: list(Category.objects.all()),
            CATEGORY_CACHE_TTL,
        )



class BookDetailView(DetailView):
    model = Book
    template_name = 'shop_app/book_detail.html'

    async def get(self, request, *args, **kwargs):
        def process_context():
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)

            context['cart_book_form'] = CartAddBookForm()
            return context

        context = await sync_to_async(process_context)()

        return self.render_to_response(context)


class BookCreateView(CreateView):
    model = Book
    template_name = 'shop_app/book_form.html'
    fields = ['title', 'author', 'category', 'description', 'price', 'stock', 'cover']
    success_url = reverse_lazy('shop_app:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    template_name = 'shop_app/book_form.html'
    fields = ['title', 'author', 'category', 'description', 'price', 'stock', 'cover']
    success_url = reverse_lazy('shop_app:book_list')

    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'shop_app/book_delete.html'
    success_url = reverse_lazy('shop_app:book_list')

    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser