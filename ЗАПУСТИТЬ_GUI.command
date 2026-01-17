#!/bin/bash
# Запуск GUI приложения для извлечения принтов

cd "$(dirname "$0")"

echo "=========================================="
echo "  ЗАПУСК GUI ПРИЛОЖЕНИЯ"
echo "=========================================="
echo ""

# Пробуем найти Python с tkinter
GUI_PYTHON=""

# Сначала пробуем системный Python (обычно имеет tkinter)
if [ -f "/usr/bin/python3" ]; then
    /usr/bin/python3 -c "import tkinter" 2>/dev/null
    if [ $? -eq 0 ]; then
        GUI_PYTHON="/usr/bin/python3"
        echo "✓ Используется системный Python с tkinter"
    fi
fi

# Если системный Python не работает, пробуем Homebrew Python
if [ -z "$GUI_PYTHON" ]; then
    PYTHON_CMD=$(which python3)
    $PYTHON_CMD -c "import tkinter" 2>/dev/null
    if [ $? -eq 0 ]; then
        GUI_PYTHON="$PYTHON_CMD"
        echo "✓ Используется Homebrew Python с tkinter"
    fi
fi

# Если tkinter не найден нигде
if [ -z "$GUI_PYTHON" ]; then
    echo "❌ tkinter не найден!"
    echo ""
    echo "РЕШЕНИЕ:"
    echo "1. Установите tkinter для Python:"
    echo "   brew install python-tk@3.14"
    echo ""
    echo "2. ИЛИ используйте консольную версию (работает без GUI):"
    echo "   ./ЗАПУСТИТЬ_ИЗВЛЕЧЕНИЕ.command"
    echo ""
    echo "3. ИЛИ используйте системный Python напрямую:"
    echo "   /usr/bin/python3 GUI_ПРИЛОЖЕНИЕ.py"
    echo ""
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Проверяем зависимости для выбранного Python
echo "Проверка зависимостей..."
$GUI_PYTHON -c "from PIL import Image; import numpy; import cv2" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Установка зависимостей для $GUI_PYTHON..."
    $GUI_PYTHON -m pip install --user --break-system-packages Pillow numpy opencv-python 2>&1 | grep -E "(Successfully|Requirement|ERROR)" | tail -5
    echo ""
fi

echo ""
echo "Запуск GUI приложения..."
echo ""

# Запускаем GUI приложение через выбранный Python (безопасная версия)
$GUI_PYTHON "GUI_РАБОТАЮЩАЯ.py"

# Если ошибка
if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске GUI приложения"
    echo ""
    echo "Используйте консольную версию:"
    echo "  ./ЗАПУСТИТЬ_ИЗВЛЕЧЕНИЕ.command"
    echo ""
    read -p "Нажмите Enter для выхода..."
fi
