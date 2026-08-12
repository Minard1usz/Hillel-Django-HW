from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse


class UserRegisterViewTest(TestCase):

    @patch("users.views.send_welcome_email_task.delay")
    def test_register_triggers_welcome_email_when_email_provided(self, mock_send_email):
        """Перевіряємо успішну реєстрацію та відправку таски в Celery"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPassword123!",
            "password2": "ComplexPassword123!",
        }

        # POST-запит на реєстрацію
        response = self.client.post(reverse("users:register"), data=user_data)

        # Форма валідна -> редірект 302
        self.assertEqual(response.status_code, 302)

        # Перевіряємо, що send_welcome_email_task.delay викликався з правильними аргументами
        mock_send_email.assert_called_once_with(
            user_email="newuser@example.com",
            subject="Ласкаво просимо до Bookstore!",
            message="Привіт, newuser! Дякуємо за реєстрацію!",
        )
