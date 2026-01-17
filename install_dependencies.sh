#!/bin/bash
# Скрипт для установки зависимостей для Homebrew Python

echo "=========================================="
echo "Установка зависимостей для программы"
echo "=========================================="
echo ""

# Определяем какой Python используется
PYTHON_CMD=$(which python3)
echo "Используется Python: $PYTHON_CMD"
echo "Версия: $($PYTHON_CMD --version)"
echo ""

# Обновляем pip (для Homebrew Python нужен флаг --break-system-packages)
echo "Обновление pip..."
$PYTHON_CMD -m pip install --upgrade pip --break-system-packages
echo ""

# Устанавливаем зависимости (используем --user для безопасности с Homebrew Python)
echo "Установка Pillow..."
$PYTHON_CMD -m pip install --user --break-system-packages Pillow

echo ""
echo "Установка numpy..."
$PYTHON_CMD -m pip install --user --break-system-packages numpy

echo ""
echo "Установка opencv-python..."
$PYTHON_CMD -m pip install --user --break-system-packages opencv-python

echo ""
echo "=========================================="
echo "Проверка установки..."
echo "=========================================="

$PYTHON_CMD -c "from PIL import Image; import numpy; import cv2; print('✓ Все модули установлены успешно!')" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Все зависимости установлены!"
    echo ""
    echo "Теперь можно запустить программу:"
    echo "  python3 console_version.py"
else
    echo ""
    echo "⚠️  Возможны проблемы с установкой"
fi
