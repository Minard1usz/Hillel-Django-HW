from django.shortcuts import render
from django.db.models import Q, Count
from .models import Book, Category
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.
def store(request):
    special_offers = Book.objects.filter(Q(price__lt=300) | Q(description__icontains='discount'))
    premium_offers = Book.objects.filter(Q(price__gt=300))
    categories_with_counts = Category.objects.annotate(total_books=Count('books'))
    available_books = Book.objects.filter(stock__gt=0)
    discount_books = Book.objects.filter(description__icontains='discount')

    context = {
        'special_offers': special_offers,
        'premium_offers': premium_offers,
        'categories': categories_with_counts,
        'available_books': available_books,
        'discount_books': discount_books,
    }
    return render(request, 'shop_app/store.html', context)

class BookListView(ListView):
    model = Book
    template_name = 'shop_app/book_list.html'
    context_object_name = 'books'
    paginate_by = 5

class BookDetailView(DetailView):
    model = Book
    template_name = 'shop_app/book_detail.html'

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