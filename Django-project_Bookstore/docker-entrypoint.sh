#!/bin/sh

# Якщо база даних ще не піднялася, ми чекаємо її, щоб Django не впав з помилкою
echo "Waiting for postgres..."

# Проста перевірка доступності порту бази за допомогою python
python -c "
import socket
import time
import os

port = int(os.environ.get('DB_PORT', 5432))
host = os.environ.get('DB_HOST', 'db')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        s.connect((host, port))
        s.close()
        break
    except socket.error:
        time.sleep(0.1)
"

echo "PostgreSQL started"

# Автоматично застосовуємо міграції
echo "Apply database migrations"
python manage.py migrate

# Збираємо статичні файли (якщо налаштовано STATIC_ROOT)
echo "Collect static files"
python manage.py collectstatic --noinput

# Запускаємо вбудований сервер Django (для розробки)
echo "Starting server"
python manage.py runserver 0.0.0.0:8000