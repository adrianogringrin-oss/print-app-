FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl-dev \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements_telegram.txt .
RUN pip install --no-cache-dir -r requirements_telegram.txt

# Копирование кода приложения (используем серверные версии без macOS-зависимостей)
COPY TELEGRAM_BOT_SERVER.py TELEGRAM_BOT.py
COPY TELEGRAM_WEBAPP_SERVER.py TELEGRAM_WEBAPP.py

# Создание директории для временных файлов
RUN mkdir -p /app/temp && chmod 777 /app/temp

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Открываем порт
EXPOSE 8080

# Команда запуска (запускаем оба сервиса через supervisor или отдельные контейнеры)
# Для простоты запускаем веб-сервер, бот будет запускаться отдельно
CMD ["python", "TELEGRAM_WEBAPP.py"]
