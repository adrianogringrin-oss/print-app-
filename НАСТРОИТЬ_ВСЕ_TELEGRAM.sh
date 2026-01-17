#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Настройка Telegram Mini App для полноценной работы..."
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

# Проверяем ngrok
if command -v ngrok &> /dev/null; then
    echo ""
    echo "🔍 Проверяю ngrok..."
    
    # Проверяем авторизацию ngrok
    if ngrok config check &>/dev/null; then
        echo "✅ ngrok настроен, запускаю туннель..."
        ngrok http 8080 > /tmp/ngrok.log 2>&1 &
        NGROK_PID=$!
        sleep 5
        
        # Получаем HTTPS URL
        HTTPS_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); tunnels = data.get('tunnels', []); https_tunnel = next((t for t in tunnels if t['proto'] == 'https'), None); print(https_tunnel['public_url'] if https_tunnel else '')" 2>/dev/null)
        
        if [ -n "$HTTPS_URL" ]; then
            export WEB_APP_URL="$HTTPS_URL"
            echo "✅ HTTPS URL получен: $HTTPS_URL"
            echo "   Сохраняю в ~/.zshrc..."
            grep -q "WEB_APP_URL" ~/.zshrc || echo "export WEB_APP_URL=\"$HTTPS_URL\"" >> ~/.zshrc
        else
            echo "⚠️  Не удалось получить HTTPS URL от ngrok"
            echo "   Используется localhost (Web App может работать не полностью)"
            export WEB_APP_URL="http://localhost:8080"
        fi
    else
        echo "⚠️  ngrok не авторизован"
        echo "   Для полноценной работы Web App:"
        echo "   1. Зарегистрируйтесь на https://dashboard.ngrok.com"
        echo "   2. Получите authtoken"
        echo "   3. Выполните: ngrok config add-authtoken YOUR_TOKEN"
        echo ""
        echo "   Пока используется localhost..."
        export WEB_APP_URL="http://localhost:8080"
    fi
else
    echo "⚠️  ngrok не установлен"
    echo "   Установите: brew install ngrok"
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
pkill ngrok 2>/dev/null
deactivate
echo "✅ Готово"
