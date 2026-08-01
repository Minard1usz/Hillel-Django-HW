import os
from celery import Celery

# Деволфтний модуль налаштувань для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')

app = Celery('bookstore_project')

# Завантаження конфігурації з settings.py з префіксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автопошук tasks.py у всіх зареєстрованих Django додатках (INSTALLED_APPS)
app.autodiscover_tasks()