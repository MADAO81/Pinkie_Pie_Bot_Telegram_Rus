# Dockerfile
# Контейнеризация бота Пинки Пай для деплоя на SprintBox
#
# Автор: MADAO81
# Версия: 2.0

FROM python:3.11-slim

LABEL maintainer="MADAO81"
LABEL version="2.0.0"
LABEL description="Telegram бот Пинки Пай с OpenAI интеграцией"

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём директории для данных
RUN mkdir -p /app/data/audio /app/logs

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["python", "run.py"]
