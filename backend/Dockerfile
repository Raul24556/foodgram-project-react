FROM python:3.9-slim-bookworm

WORKDIR /app

# Установка зависимостей для компиляции psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Обновление pip и установка зависимостей
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Настройка окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Запуск Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "foodgram.wsgi:application"]
