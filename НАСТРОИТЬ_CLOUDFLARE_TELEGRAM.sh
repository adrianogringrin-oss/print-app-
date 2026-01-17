#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Настройка Telegram Mini App с Cloudflare Tunnel..."
echo ""

# Устанавливаем переменные окружения
export TELEGRAM_BOT_TOKEN="8587425740:AAG1zY9gROId5uNDQFrRruB5PdOOQd2ErlQ"

# Проверяем виртуальное окружение
if [ ! -d "venv_telegram" ]; then
    echo "📦 Создаю виртуальное окружение..."
    ./УСТАНОВИТЬ_TELEGRAM.sh
fi

source venv_telegram/bin/activate

# Останавливаем старые процессы
echo "🛑 Останавливаю старые процессы..."
pkill -f TELEGRAM_BOT 2>/dev/null
pkill -f TELEGRAM_WEBAPP 2>/dev/null
pkill ngrok 2>/dev/null
pkill cloudflared 2>/dev/null
sleep 2

# Запускаем веб-сервер
echo "🌐 Запускаю веб-сервер..."
python TELEGRAM_WEBAPP.py > /tmp/telegram_webapp.log 2>&1 &
WEBAPP_PID=$!
sleep 3

if ! kill -0 $WEBAPP_PID 2>/dev/null; then
    echo "❌ Ошибка запуска веб-сервера!"
    exit 1
fi

echo "✅ Веб-сервер запущен (PID: $WEBAPP_PID)"

# Проверяем и запускаем Cloudflare Tunnel
echo ""
echo "☁️  Проверяю Cloudflare Tunnel..."

if command -v cloudflared &> /dev/null; then
    echo "✅ cloudflared установлен, запускаю туннель..."
    cloudflared tunnel --url http://localhost:8080 > /tmp/cloudflared.log 2>&1 &
    CLOUDFLARE_PID=$!
    sleep 5
    
    # Получаем HTTPS URL из логов (ждем появления URL)
    HTTPS_URL=""
    for i in {1..10}; do
        HTTPS_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log 2>/dev/null | head -1)
        if [ -n "$HTTPS_URL" ]; then
            break
        fi
        sleep 1
    done
    
    if [ -n "$HTTPS_URL" ]; then
        export WEB_APP_URL="$HTTPS_URL"
        echo "✅ HTTPS URL получен: $HTTPS_URL"
        echo "   Сохраняю в ~/.zshrc..."
        grep -q "WEB_APP_URL" ~/.zshrc || echo "export WEB_APP_URL=\"$HTTPS_URL\"" >> ~/.zshrc
        echo "$HTTPS_URL" > /tmp/cloudflare_url.txt
    else
        echo "⚠️  Не удалось получить HTTPS URL от Cloudflare Tunnel"
        echo "   Проверьте логи: cat /tmp/cloudflared.log"
        echo "   Используется localhost (Web App может работать не полностью)"
        export WEB_APP_URL="http://localhost:8080"
    fi
else
    echo "⚠️  cloudflared не установлен"
    echo "   Установите: brew install cloudflared"
    echo "   Пока используется localhost..."
    export WEB_APP_URL="http://localhost:8080"
fi

# Запускаем бота
echo ""
echo "🤖 Запускаю Telegram бота..."
echo "   Web App URL: $WEB_APP_URL"
echo ""
echo "📱 Инструкция:"
echo "   1. Найдите бота в Telegram"
echo "   2. Отправьте /start"
echo "   3. Загрузите изображение"
echo ""
echo "🛑 Для остановки нажмите Ctrl+C"
echo ""

python TELEGRAM_BOT.py

# Очистка при выходе
echo ""
echo "🛑 Останавливаю процессы..."
kill $WEBAPP_PID 2>/dev/null
pkill cloudflared 2>/dev/null
deactivate
echo "✅ Готово"
