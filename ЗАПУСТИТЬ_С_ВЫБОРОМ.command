#!/bin/bash
# Запуск версии с интерактивным выбором области мышью

cd "$(dirname "$0")"

echo "Запуск программы с выбором области..."
echo ""

# Используем системный Python
PYTHON_CMD="/usr/bin/python3"

# Очищаем окружение
unset PYTHONPATH
export PYTHONPATH=""

# Запускаем
"$PYTHON_CMD" GUI_ВЫБОР_ОБЛАСТИ.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске"
    read -p "Нажмите Enter для выхода..."
fi
