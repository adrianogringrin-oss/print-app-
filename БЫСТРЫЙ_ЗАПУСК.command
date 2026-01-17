#!/bin/bash
# Быстрый запуск программы с автоматической установкой зависимостей

cd "$(dirname "$0")"

echo "=========================================="
echo "  ПРОГРАММА ДЛЯ ИЗВЛЕЧЕНИЯ ПРИНТОВ"
echo "=========================================="
echo ""

# Определяем Python
PYTHON_CMD=$(which python3)
echo "Используется Python: $PYTHON_CMD"
echo "Версия: $($PYTHON_CMD --version)"
echo ""

# Проверяем зависимости
echo "Проверка зависимостей..."
MISSING=0

$PYTHON_CMD -c "from PIL import Image" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ Pillow не установлен"
    MISSING=1
else
    echo "✓ Pillow установлен"
fi

$PYTHON_CMD -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ numpy не установлен"
    MISSING=1
else
    echo "✓ numpy установлен"
fi

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "Установка недостающих зависимостей..."
    echo ""
    $PYTHON_CMD -m pip install --upgrade pip --break-system-packages
    echo ""
    echo "Установка Pillow, numpy, opencv-python..."
    $PYTHON_CMD -m pip install --user --break-system-packages Pillow numpy opencv-python
    echo ""
    echo "Проверка установки..."
    $PYTHON_CMD -c "from PIL import Image; import numpy; import cv2; print('✓ Все модули установлены!')" 2>&1
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Ошибка установки. Попробуйте установить вручную:"
        echo "  $PYTHON_CMD -m pip install --user --break-system-packages Pillow numpy opencv-python"
        echo ""
        echo "Или используйте виртуальное окружение:"
        echo "  $PYTHON_CMD -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install Pillow numpy opencv-python"
        echo ""
        read -p "Нажмите Enter для выхода..."
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "  ЗАПУСК ПРОГРАММЫ"
echo "=========================================="
echo ""

# Запускаем программу
$PYTHON_CMD "ПРОСТАЯ_ВЕРСИЯ.py"

# Если ошибка
if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске программы"
    read -p "Нажмите Enter для выхода..."
fi
