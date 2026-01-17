#!/bin/bash
# Прямой запуск GUI с очищенным окружением

cd "$(dirname "$0")"

echo "Запуск GUI приложения с очищенным окружением..."
echo ""

# Очищаем все переменные Python
unset PYTHONPATH
unset PYTHONHOME
export PYTHONPATH=""

# Используем системный Python
PYTHON_CMD="/usr/bin/python3"

# Запускаем с полностью очищенным окружением
env -i \
    PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
    HOME="$HOME" \
    USER="$USER" \
    SHELL="$SHELL" \
    "$PYTHON_CMD" GUI_БЕЗ_ИЗОБРАЖЕНИЙ.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Ошибка при запуске"
    read -p "Нажмите Enter для выхода..."
fi
