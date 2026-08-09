#!/bin/sh

# Якщо DB_HOST або DB_PORT не задані у змінних оточення, беремо дефолтні значення
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

echo "Waiting for postgres at $DB_HOST:$DB_PORT..."

# Чекаємо підключення до сокета бази даних
while ! python -c "
import socket, os, sys
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('$DB_HOST', int('$DB_PORT')))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done

echo "PostgreSQL started successfully!"

echo "Apply database migrations..."
python manage.py migrate --noinput

echo "Collect static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn server..."
# exec ОБОВ'ЯЗКОВО має бути ОСТАННЬОЮ командою в скрипті!
exec gunicorn bookstore_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3