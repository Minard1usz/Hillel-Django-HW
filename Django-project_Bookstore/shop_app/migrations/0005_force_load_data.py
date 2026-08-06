import os
from django.core.management import call_command
from django.db import migrations


def load_books_data(apps, schema_editor):
    fixture_path = "shop_app/fixtures/books_data.json"

    print(f"===> STARTING LOAD DATA FROM: {fixture_path}")

    # Перевірка наявності файла
    if not os.path.exists(fixture_path):
        print(f"===> ERROR: File {fixture_path} NOT FOUND in container!")
        return

    try:
        call_command("loaddata", fixture_path)
        print("===> SUCCESS: Books data loaded successfully into PostgreSQL!")
    except Exception as e:
        print(f"===> ERROR during loaddata execution: {e}")


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shop_app", "0003_alter_book_options_alter_category_options"),
    ]

    operations = [
        migrations.RunPython(load_books_data, reverse_code=reverse_func),
    ]