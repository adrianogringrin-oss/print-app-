#!/bin/bash
# Запуск веб-версии с ИИ поддержкой

cd "$(dirname "$0")"

echo "Запуск веб-версии с ИИ..."
echo ""

# Проверяем OpenAI
if ! python3 -c "import openai" 2>/dev/null; then
    echo "⚠ OpenAI не установлен"
    echo "Установите: pip3 install openai"
    echo ""
    echo "Продолжаю запуск без ИИ функций..."
    echo ""
fi

# Используем Homebrew Python (там все библиотеки установлены)
PYTHON_CMD=$(which python3)

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3 не найден!"
    exit 1
fi

echo "Используется Python: $PYTHON_CMD"
echo ""

# Проверяем что все библиотеки доступны
if ! "$PYTHON_CMD" -c "import openai; from PIL import Image; print('✅ Все библиотеки доступны')" 2>/dev/null; then
    echo "⚠ Проверка библиотек не прошла, но продолжаю запуск..."
    echo "   Если будут ошибки, установите: python3 -m pip install --user --break-system-packages Pillow openai"
    echo ""
fi

# Запускаем веб-сервер
"$PYTHON_CMD" ВЕБ_ВЕРСИЯ_С_ИИ.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске"
    read -p "Нажмите Enter для выхода..."
fi
