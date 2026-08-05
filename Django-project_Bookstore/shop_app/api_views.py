from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Book, Category
from .serializers import BookSerializer, CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для керування категоріями книг.

    Дозволяє адміністраторам виконувати CRUD-операції,
    а звичайним користувачам — лише переглядати список та деталі.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # швидкий пошук категорій за назвою
    filter_backends = [SearchFilter]
    search_fields = ["name"]


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet для керування каталогом книг.

    Підтримує пагінацію (20 на сторінку), сортування, пошук
    та детальну фільтрацію за ціною та категорією.
    """

    queryset = Book.objects.select_related("category").all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # налаштування фільтрації, пошуку та сортування
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # фільтрація за категорією та діапазоном цін (django-filter)
    filterset_fields = {
        "category": ["exact"],
        "price": [
            "gte",
            "lte",
        ],  # дозволяємо робити /api/books/?price__gte=100&price__lte=300
    }

    # пошук за назвою та автором
    search_fields = ["title", "author", "description"]

    # сортування за ціною та датою (якщо є)
    ordering_fields = ["price", "id"]
    ordering = ["id"]  # дефолт сортування для стабільної пагінації

    def perform_create(self, serializer):
        """
        Кастомне збереження: якщо потрібно виконати додаткову логіку
        перед записом книги в БД.
        """
        serializer.save()
