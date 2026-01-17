#!/bin/bash
cd "$(dirname "$0")"

echo "📦 Установка зависимостей для Telegram Mini App..."
echo ""

# Создаем виртуальное окружение
if [ ! -d "venv_telegram" ]; then
    echo "Создаю виртуальное окружение..."
    python3 -m venv venv_telegram
fi

# Активируем виртуальное окружение
source venv_telegram/bin/activate

echo "Устанавливаю зависимости..."
pip install --upgrade pip
pip install -r requirements_telegram.txt

echo ""
echo "Проверяю установку..."
python -c "
try:
    import telegram
    print('✅ python-telegram-bot установлен:', telegram.__version__)
except ImportError:
    print('❌ python-telegram-bot не установлен')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Все зависимости установлены в виртуальное окружение!"
    echo ""
    echo "📖 Следующие шаги:"
    echo "   1. Создайте бота у @BotFather в Telegram"
    echo "   2. Установите переменные окружения:"
    echo "      export TELEGRAM_BOT_TOKEN='ваш_токен'"
    echo "      export WEB_APP_URL='https://your-domain.com'"
    echo "   3. Запустите: ./ЗАПУСТИТЬ_TELEGRAM.command"
    echo ""
    echo "💡 Виртуальное окружение создано в: venv_telegram/"
    echo "   Для активации: source venv_telegram/bin/activate"
else
    echo ""
    echo "❌ Ошибка установки"
fi

deactivate
