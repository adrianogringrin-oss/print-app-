#!/bin/bash
# Простой скрипт запуска для macOS/Linux

cd "$(dirname "$0")"
python3 запустить.py

# Если окно закрывается сразу, добавьте задержку
if [ $? -ne 0 ]; then
    echo ""
    echo "Нажмите Enter для выхода..."
    read
fi
