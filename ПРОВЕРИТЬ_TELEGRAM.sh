#!/bin/bash
cd "$(dirname "$0")"

echo "🔍 Проверка Telegram Mini App..."
echo ""

# Проверка файлов
echo "📁 Проверка файлов:"
files=("TELEGRAM_BOT.py" "TELEGRAM_WEBAPP.py" "requirements_telegram.txt" "ИНСТРУКЦИЯ_TELEGRAM.txt")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - НЕ НАЙДЕН!"
    fi
done
echo ""

# Проверка зависимостей
echo "📦 Проверка зависимостей:"
if [ -d "venv_telegram" ]; then
    source venv_telegram/bin/activate
    python -c "import telegram" 2>/dev/null && echo "  ✅ python-telegram-bot (в venv_telegram)" || echo "  ❌ python-telegram-bot - НЕ УСТАНОВЛЕН"
    python -c "from PIL import Image" 2>/dev/null && echo "  ✅ Pillow (в venv_telegram)" || echo "  ❌ Pillow - НЕ УСТАНОВЛЕН"
    python -c "import openai" 2>/dev/null && echo "  ✅ openai (в venv_telegram)" || echo "  ⚠️  openai - НЕ УСТАНОВЛЕН (ИИ функции недоступны)"
    deactivate
else
    python3 -c "import telegram" 2>/dev/null && echo "  ✅ python-telegram-bot" || echo "  ❌ python-telegram-bot - НЕ УСТАНОВЛЕН (создайте venv: ./УСТАНОВИТЬ_TELEGRAM.sh)"
    python3 -c "from PIL import Image" 2>/dev/null && echo "  ✅ Pillow" || echo "  ❌ Pillow - НЕ УСТАНОВЛЕН"
    python3 -c "import openai" 2>/dev/null && echo "  ✅ openai" || echo "  ⚠️  openai - НЕ УСТАНОВЛЕН (ИИ функции недоступны)"
fi
echo ""

# Проверка переменных окружения
echo "🔧 Проверка переменных окружения:"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "  ❌ TELEGRAM_BOT_TOKEN - НЕ УСТАНОВЛЕН"
    echo "     Установите: export TELEGRAM_BOT_TOKEN='ваш_токен'"
else
    echo "  ✅ TELEGRAM_BOT_TOKEN установлен"
fi

if [ -z "$WEB_APP_URL" ]; then
    echo "  ⚠️  WEB_APP_URL - НЕ УСТАНОВЛЕН"
    echo "     Для тестирования используйте ngrok"
    echo "     Установите: export WEB_APP_URL='https://your-domain.com'"
else
    echo "  ✅ WEB_APP_URL установлен: $WEB_APP_URL"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "  ⚠️  OPENAI_API_KEY - НЕ УСТАНОВЛЕН (ИИ функции недоступны)"
else
    echo "  ✅ OPENAI_API_KEY установлен"
fi
echo ""

# Проверка синтаксиса Python
echo "🐍 Проверка синтаксиса Python:"
python3 -m py_compile TELEGRAM_BOT.py 2>/dev/null && echo "  ✅ TELEGRAM_BOT.py - синтаксис корректен" || echo "  ❌ TELEGRAM_BOT.py - ошибка синтаксиса"
python3 -m py_compile TELEGRAM_WEBAPP.py 2>/dev/null && echo "  ✅ TELEGRAM_WEBAPP.py - синтаксис корректен" || echo "  ❌ TELEGRAM_WEBAPP.py - ошибка синтаксиса"
echo ""

# Проверка порта
echo "🌐 Проверка порта 8080:"
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "  ⚠️  Порт 8080 занят"
    echo "     Остановите другие процессы или измените порт в TELEGRAM_WEBAPP.py"
else
    echo "  ✅ Порт 8080 свободен"
fi
echo ""

echo "✅ Проверка завершена!"
echo ""
echo "📖 Следующие шаги:"
echo "   1. Установите зависимости: pip3 install -r requirements_telegram.txt"
echo "   2. Создайте бота у @BotFather"
echo "   3. Настройте переменные окружения"
echo "   4. Запустите: ./ЗАПУСТИТЬ_TELEGRAM.command"
echo ""
