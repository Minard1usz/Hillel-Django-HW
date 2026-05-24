from django.urls import path
from .views import store, BookListView, BookDetailView, BookCreateView, BookUpdateView, BookDeleteView

app_name = 'shop_app'

urlpatterns = [
    path('', store, name='store'),
    path('catalog/', BookListView.as_view(), name='book_list'),
    path('<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    path('book/create/', BookCreateView.as_view(), name='book_create'),
    path('book/<int:pk>/update/', BookUpdateView.as_view(), name='book_update'),
    path('book/<int:pk>/delete/', BookDeleteView.as_view(), name='book_delete'),
]