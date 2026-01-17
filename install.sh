#!/bin/bash
# Скрипт для установки зависимостей

echo "Установка зависимостей для программы извлечения принтов..."
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

echo "Python найден: $(python3 --version)"
echo ""

# Обновление pip
echo "Обновление pip..."
python3 -m pip install --upgrade pip

# Установка зависимостей
echo ""
echo "Установка зависимостей из requirements.txt..."
python3 -m pip install -r requirements.txt

echo ""
echo "Установка завершена!"
echo ""
echo "Для запуска программы используйте:"
echo "python3 main.py"
