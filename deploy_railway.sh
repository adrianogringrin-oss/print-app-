#!/bin/bash
# Скрипт для развертывания на Railway

echo "🚀 Развертывание на Railway"
echo ""

# Проверяем наличие Railway CLI
if ! command -v railway &> /dev/null; then
    echo "📦 Установка Railway CLI..."
    npm install -g @railway/cli
fi

# Проверяем переменные окружения
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен"
    echo "   Установите: export TELEGRAM_BOT_TOKEN=ваш_токен"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY не установлен"
    echo "   Установите: export OPENAI_API_KEY=ваш_ключ"
    exit 1
fi

echo "✅ Переменные окружения проверены"
echo ""

# Логин в Railway
echo "🔐 Вход в Railway..."
railway login

# Создаем проект
echo "📦 Создание проекта..."
railway init

# Устанавливаем переменные окружения
echo "⚙️  Настройка переменных окружения..."
railway variables set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set PORT=8080

# Деплой
echo "🚀 Запуск деплоя..."
railway up

# Получаем URL
echo ""
echo "⏳ Ожидание получения URL..."
sleep 5
WEB_APP_URL=$(railway domain)

if [ -n "$WEB_APP_URL" ]; then
    echo "✅ URL получен: $WEB_APP_URL"
    railway variables set WEB_APP_URL="https://$WEB_APP_URL"
    echo ""
    echo "✅ Развертывание завершено!"
    echo "📱 URL приложения: https://$WEB_APP_URL"
    echo ""
    echo "📝 Следующие шаги:"
    echo "   1. Откройте @BotFather в Telegram"
    echo "   2. Отправьте /setmenubutton"
    echo "   3. Выберите вашего бота"
    echo "   4. Введите URL: https://$WEB_APP_URL"
else
    echo "⚠️  URL не получен автоматически"
    echo "   Получите URL вручную в панели Railway и установите:"
    echo "   railway variables set WEB_APP_URL=https://ваш_домен.railway.app"
fi
