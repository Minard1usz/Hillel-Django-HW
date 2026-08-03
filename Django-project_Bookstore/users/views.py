from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from shop_app.tasks import send_welcome_email_task

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

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.object.email:
            send_welcome_email_task.delay(
                user_email=self.object.mail,
                subject="Ласкаво просимо до Bookstore!",
                message=f"Привіт, {self.object.username}! Дякуємо за реєстрацію!"
            )
        return response

