#!/bin/bash
# Скрипт для запуска программы извлечения принтов

cd "$(dirname "$0")"

echo "=========================================="
echo "  ЗАПУСК ПРОГРАММЫ ИЗВЛЕЧЕНИЯ ПРИНТОВ"
echo "=========================================="
echo ""

# Определяем Python
PYTHON_CMD=$(which python3)

# Проверяем зависимости
echo "Проверка зависимостей..."
$PYTHON_CMD -c "from PIL import Image; import numpy" 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Установка недостающих зависимостей..."
    $PYTHON_CMD -m pip install --user --break-system-packages Pillow numpy opencv-python 2>&1 | grep -E "(Successfully|Requirement|ERROR)" | tail -5
    echo ""
fi

echo ""
echo "Запуск программы..."
echo ""

# Запускаем программу
$PYTHON_CMD "ИЗВЛЕЧЕНИЕ_ПРИНТА.py"

# Если ошибка
if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске программы"
    read -p "Нажмите Enter для выхода..."
fi
