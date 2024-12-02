# Изображение с Python
FROM python:3.12-slim

# Установим необходимые зависимости для работы с PostgreSQL и Redis
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем и переходим в рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения в контейнер
COPY . /app/

# Устанавливаем переменную окружения для управления приложением
ENV PYTHONUNBUFFERED 1

# Открываем порт для веб-сервера
EXPOSE 8000

# Выполняем миграции перед запуском приложения
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn referral_system.wsgi:application --bind 0.0.0.0:8000"]
