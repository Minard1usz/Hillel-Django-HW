from unittest.mock import patch
from django.conf import settings
from django.test import TestCase
from shop_app.tasks import (
    send_welcome_email_task,
    generate_report_task,
    clear_expired_sessions_task,
)


class CeleryTasksTests(TestCase):

    @patch("shop_app.tasks.send_mail")
    def test_send_welcome_email_task(self, mock_send_mail):
        """Тест асинхронної відправки email (з моком send_mail)."""
        result = send_welcome_email_task(
            user_email="test@example.com",
            subject="Ласкаво просимо!",
            message="Дякуємо за реєстрацію.",
        )

        expected_from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"
        )

        # Перевіряємо, що send_mail дійсно викликався з правильними аргументами
        mock_send_mail.assert_called_once_with(
            subject="Ласкаво просимо!",
            message="Дякуємо за реєстрацію.",
            from_email=expected_from_email,
            recipient_list=["test@example.com"],
            fail_silently=False,
        )
        self.assertEqual(result, "Email sent to test@example.com")

    @patch(
        "time.sleep", return_value=None
    )  # Мокаємо sleep, щоб тест не чекав 5 секунд!
    def test_generate_report_task(self, mock_sleep):
        """Тест генерації звітів."""
        result = generate_report_task()

        mock_sleep.assert_called_once_with(5)
        self.assertEqual(result, "Report generated")

    @patch("shop_app.tasks.call_command")
    def test_clear_expired_sessions_task(self, mock_call_command):
        """Тест очищення сесій через management-команду."""
        result = clear_expired_sessions_task()

        mock_call_command.assert_called_once_with("clearsessions")
        self.assertEqual(result, "Sessions cleared")
