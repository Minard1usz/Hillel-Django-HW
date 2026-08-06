import sys
from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = "shop_app"

class ShopAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop_app"

    def ready(self):
        if "gunicorn" in sys.argv or "runserver" in sys.argv:
            from django.core.management import call_command

            try:
                call_command("migrate", interactive=False)
            except Exception as e:
                print(f"Migration error on startup: {e}")