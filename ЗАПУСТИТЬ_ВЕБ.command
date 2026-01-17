#!/bin/bash
# Запуск веб-версии - работает в браузере, нет крашей!

cd "$(dirname "$0")"

echo "Запуск веб-версии программы..."
echo ""

# Используем системный Python
PYTHON_CMD="/usr/bin/python3"

# Очищаем окружение
unset PYTHONPATH
export PYTHONPATH=""

# Запускаем веб-сервер
"$PYTHON_CMD" ВЕБ_ВЕРСИЯ.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске"
    read -p "Нажмите Enter для выхода..."
fi
