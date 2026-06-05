# Базовий образ з Python
FROM python:3.12-slim

# Встановлюємо системні залежності, необхідні для роботи Postgres драйвера та компіляції
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Налаштовуємо робочу директорію всередині контейнера
WORKDIR /app

# Змінні оточення, щоб Python не писав .pyc файли і не буферизував логі
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копіюємо та встановлюємо залежності
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо весь код проєкту в контейнер
COPY . /app/

# Робимо наш майбутній скрипт запуску виконуваним
RUN chmod +x /app/docker-entrypoint.sh

# Вказуємо точку входу
ENTRYPOINT ["/app/docker-entrypoint.sh"]