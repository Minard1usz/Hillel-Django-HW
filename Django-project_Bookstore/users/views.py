from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm

# Create your views here.
class RegisterView(CreateView):
    """
        Class-Based View для реєстрації нових користувачів у системі.

        Використовує кастомну форму `CustomUserCreationForm` для збору даних
        (наприклад, email, пароль, ім'я) та створення нового запису користувача в БД.
        Після успішної реєстрації автоматично перенаправляє користувача
        на сторінку автентифікації (`users:login`).
        """
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

