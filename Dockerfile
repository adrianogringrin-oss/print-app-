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

# Копирование кода приложения (имена файлов должны совпадать с railway.json startCommand)
COPY TELEGRAM_BOT_SERVER.py .
COPY TELEGRAM_WEBAPP_SERVER.py .

# Создание директории для временных файлов
RUN mkdir -p /app/temp && chmod 777 /app/temp

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Открываем порт
EXPOSE 8080

# CMD переопределяется railway.json startCommand (раздельный запуск webapp/bot по SERVICE_TYPE)
CMD ["python", "TELEGRAM_WEBAPP_SERVER.py"]
