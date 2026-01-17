#!/bin/bash
# Запуск GUI с выводом ошибок в файл для отладки

cd "$(dirname "$0")"

LOG_FILE="gui_errors.log"

echo "Запуск GUI приложения..."
echo "Ошибки будут сохранены в: $LOG_FILE"
echo ""

# Определяем Python
PYTHON_CMD="/usr/bin/python3"

if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD=$(which python3)
fi

# Запускаем с выводом ошибок
"$PYTHON_CMD" GUI_РАБОТАЮЩАЯ.py 2>&1 | tee "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске. Смотрите лог: $LOG_FILE"
    read -p "Нажмите Enter для выхода..."
fi
