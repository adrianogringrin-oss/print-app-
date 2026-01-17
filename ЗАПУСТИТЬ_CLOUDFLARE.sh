#!/bin/bash
cd "$(dirname "$0")"

echo "☁️  Запуск Cloudflare Tunnel..."
echo ""

# Останавливаем старые процессы
pkill -f cloudflared 2>/dev/null
pkill -f TELEGRAM_WEBAPP 2>/dev/null
sleep 2

# Проверяем установку cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared не установлен!"
    echo "   Установите: brew install cloudflared"
    exit 1
fi

# Запускаем веб-сервер если не запущен
if ! lsof -i :8080 | grep -q LISTEN; then
    echo "🌐 Запускаю веб-сервер..."
    cd "$(dirname "$0")"
    if [ -d "venv_telegram" ]; then
        source venv_telegram/bin/activate
        python TELEGRAM_WEBAPP.py > /tmp/telegram_webapp.log 2>&1 &
        sleep 3
    else
        echo "⚠️  Виртуальное окружение не найдено"
        echo "   Запустите: ./УСТАНОВИТЬ_TELEGRAM.sh"
    fi
fi

# Запускаем Cloudflare Tunnel
echo "☁️  Запускаю Cloudflare Tunnel..."
echo "   Это может занять несколько секунд..."
echo ""

# Запускаем tunnel в фоне и получаем URL
cloudflared tunnel --url http://localhost:8080 > /tmp/cloudflared.log 2>&1 &
CLOUDFLARE_PID=$!
sleep 5

# Извлекаем URL из логов (ждем появления URL)
HTTPS_URL=""
for i in {1..15}; do
    HTTPS_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log 2>/dev/null | head -1)
    if [ -n "$HTTPS_URL" ]; then
        break
    fi
    sleep 1
done

if [ -n "$HTTPS_URL" ]; then
    echo "✅ Cloudflare Tunnel запущен!"
    echo "   URL: $HTTPS_URL"
    echo ""
    echo "📋 Установите переменную окружения:"
    echo "   export WEB_APP_URL=\"$HTTPS_URL\""
    echo ""
    echo "   Или добавьте в ~/.zshrc:"
    echo "   echo 'export WEB_APP_URL=\"$HTTPS_URL\"' >> ~/.zshrc"
    echo ""
    echo "🛑 Для остановки нажмите Ctrl+C или выполните:"
    echo "   pkill cloudflared"
    echo ""
    
    # Сохраняем URL в файл для использования другими скриптами
    echo "$HTTPS_URL" > /tmp/cloudflare_url.txt
    
    # Ждем завершения
    wait $CLOUDFLARE_PID
else
    echo "⚠️  Не удалось получить URL от Cloudflare Tunnel"
    echo "   Проверьте логи: cat /tmp/cloudflared.log"
    kill $CLOUDFLARE_PID 2>/dev/null
    exit 1
fi
