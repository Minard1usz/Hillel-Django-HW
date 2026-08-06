import os
import sys
from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = "shop_app"

class ShopAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop_app"

    def ready(self):
        is_server = any(cmd in sys.argv[0] for cmd in ["gunicorn", "runserver"])

        if is_server and os.environ.get("RUN_MAIN") != "true":
            from django.core.management import call_command

            try:
                print("==> Auto-running migrations on server startup...")
                call_command("migrate", interactive=False)
                print("==> Migrations completed successfully!")
            except Exception as e:
                print(f"==> Migration failed: {e}")