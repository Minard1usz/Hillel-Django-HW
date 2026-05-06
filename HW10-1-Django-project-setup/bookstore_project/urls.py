from django.contrib import admin
from django.urls import path
from shop.views import store_index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', store_index, name='home')
]
