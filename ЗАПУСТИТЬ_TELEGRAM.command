#!/bin/bash
cd "$(dirname "$0")"

echo "🤖 Запуск Telegram Mini App..."
echo ""

# Проверяем виртуальное окружение
if [ ! -d "venv_telegram" ]; then
    echo "⚠️  Виртуальное окружение не найдено!"
    echo "   Запустите: ./УСТАНОВИТЬ_TELEGRAM.sh"
    exit 1
fi

# Активируем виртуальное окружение
source venv_telegram/bin/activate

# Проверяем переменные окружения
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен!"
    echo "   Установите: export TELEGRAM_BOT_TOKEN='ваш_токен'"
    echo "   Получите токен у @BotFather в Telegram"
    deactivate
    exit 1
fi

if [ -z "$WEB_APP_URL" ]; then
    echo "⚠️  WEB_APP_URL не установлен!"
    echo "   Для тестирования используйте ngrok:"
    echo "   1. Запустите: python3 TELEGRAM_WEBAPP.py"
    echo "   2. В другом терминале: ngrok http 8080"
    echo "   3. Скопируйте HTTPS URL и установите: export WEB_APP_URL='https://...'"
    echo ""
    echo "   Продолжаем с localhost для тестирования..."
    export WEB_APP_URL="http://localhost:8080"
fi

# Проверяем зависимости
echo "📦 Проверка зависимостей..."
python -c "import telegram" 2>/dev/null || {
    echo "❌ python-telegram-bot не установлен!"
    echo "   Запустите: ./УСТАНОВИТЬ_TELEGRAM.sh"
    deactivate
    exit 1
}

python3 -c "from PIL import Image" 2>/dev/null || {
    echo "❌ Pillow не установлен!"
    echo "   Установите: pip3 install Pillow"
    exit 1
}

echo "✅ Зависимости установлены"
echo ""

# Запускаем веб-сервер в фоне
echo "🌐 Запуск веб-сервера..."
python TELEGRAM_WEBAPP.py > /tmp/telegram_webapp.log 2>&1 &
WEBAPP_PID=$!
sleep 2

# Проверяем, что веб-сервер запустился
if ! kill -0 $WEBAPP_PID 2>/dev/null; then
    echo "❌ Ошибка запуска веб-сервера!"
    echo "   Проверьте логи: cat /tmp/telegram_webapp.log"
    deactivate
    exit 1
fi

echo "✅ Веб-сервер запущен (PID: $WEBAPP_PID)"
echo ""

# Запускаем бота
echo "🤖 Запуск Telegram бота..."
echo "   Нажмите Ctrl+C для остановки"
echo ""

python TELEGRAM_BOT.py

# Останавливаем веб-сервер при выходе
echo ""
echo "🛑 Остановка веб-сервера..."
kill $WEBAPP_PID 2>/dev/null
deactivate
echo "✅ Готово"
