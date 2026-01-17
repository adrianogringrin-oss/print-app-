#!/bin/bash
# Скрипт для подготовки к развертыванию - удаляет macOS-зависимости

echo "🔧 Подготовка к развертыванию на сервере..."
echo ""

# Создаем копии файлов без macOS-зависимостей
echo "📝 Создание серверных версий файлов..."

# Обрабатываем TELEGRAM_BOT.py
if [ -f "TELEGRAM_BOT.py" ]; then
    # Удаляем строки с macOS-путями
    grep -v "user_site_314\|Library/Python" TELEGRAM_BOT.py > TELEGRAM_BOT_SERVER.py.tmp
    # Удаляем пустые строки после удаления
    sed '/^$/N;/^\n$/d' TELEGRAM_BOT_SERVER.py.tmp > TELEGRAM_BOT_SERVER.py
    rm TELEGRAM_BOT_SERVER.py.tmp
    echo "✅ TELEGRAM_BOT_SERVER.py создан"
else
    echo "⚠️  TELEGRAM_BOT.py не найден"
fi

# Обрабатываем TELEGRAM_WEBAPP.py
if [ -f "TELEGRAM_WEBAPP.py" ]; then
    # Удаляем строки с macOS-путями
    grep -v "user_site_314\|Library/Python" TELEGRAM_WEBAPP.py > TELEGRAM_WEBAPP_SERVER.py.tmp
    # Удаляем пустые строки после удаления
    sed '/^$/N;/^\n$/d' TELEGRAM_WEBAPP_SERVER.py.tmp > TELEGRAM_WEBAPP_SERVER.py
    rm TELEGRAM_WEBAPP_SERVER.py.tmp
    echo "✅ TELEGRAM_WEBAPP_SERVER.py создан"
else
    echo "⚠️  TELEGRAM_WEBAPP.py не найден"
fi

echo ""
echo "✅ Подготовка завершена!"
echo ""
echo "📁 Файлы готовы к развертыванию:"
echo "   - TELEGRAM_BOT_SERVER.py"
echo "   - TELEGRAM_WEBAPP_SERVER.py"
echo "   - requirements_telegram.txt"
echo "   - Dockerfile"
echo "   - docker-compose.yml"
echo ""
echo "📖 См. РАЗВЕРТЫВАНИЕ_НА_СЕРВЕРЕ.md для инструкций"
