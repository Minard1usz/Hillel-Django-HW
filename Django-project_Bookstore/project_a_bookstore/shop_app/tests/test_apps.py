from unittest.mock import patch
import sys
from django.test import TestCase
from shop_app.apps import ShopAppConfig


class ShopAppConfigTest(TestCase):

    def test_apps_ready_runs_migrations_on_server_start(self):
        """Перевіряємо, що ready() виконує міграції при старті сервера"""
        app_config = ShopAppConfig("shop_app", sys.modules[__name__])

        # Симулюємо sys.argv[0], у якому є "runserver"
        with patch.object(sys, "argv", ["runserver"]):
            with patch("os.environ.get", return_value=None):
                with patch("django.core.management.call_command") as mock_call_command:
                    app_config.ready()

                    mock_call_command.assert_called_once_with(
                        "migrate", interactive=False
                    )

    def test_apps_ready_handles_migration_exception(self):
        """Перевіряємо обробку помилки (блок except Exception) у ready()"""
        app_config = ShopAppConfig("shop_app", sys.modules[__name__])

        with patch.object(sys, "argv", ["runserver"]):
            with patch("os.environ.get", return_value=None):
                with patch(
                    "django.core.management.call_command",
                    side_effect=Exception("DB Error"),
                ):
                    # Метод не повинен впасти через Exception завдяки try-except
                    app_config.ready()
