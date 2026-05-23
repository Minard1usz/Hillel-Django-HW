from django.shortcuts import render
from django.db.models import Q
from django.db.models import Count
from .models import Book, Category

# Create your views here.
def store_index(request):
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
    return render(request, 'store.html', context)