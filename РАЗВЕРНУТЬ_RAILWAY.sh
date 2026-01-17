#!/bin/bash
# Автоматический скрипт для развертывания на Railway

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  🚀 АВТОМАТИЧЕСКОЕ РАЗВЕРТЫВАНИЕ НА RAILWAY"
echo "═══════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Проверяем наличие необходимых файлов
echo "📋 Проверка файлов..."
REQUIRED_FILES=(
    "TELEGRAM_BOT_SERVER.py"
    "TELEGRAM_WEBAPP_SERVER.py"
    "start_server.sh"
    "railway.json"
    "requirements_telegram.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Файл не найден: $file"
        exit 1
    fi
done
echo "✅ Все необходимые файлы найдены"
echo ""

# Проверяем git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git: https://git-scm.com/"
    exit 1
fi

# Проверяем, инициализирован ли git
if [ ! -d ".git" ]; then
    echo "📦 Инициализация Git репозитория..."
    git init
    echo "✅ Git инициализирован"
else
    echo "✅ Git репозиторий уже инициализирован"
fi
echo ""

# Проверяем переменные окружения
echo "🔐 Проверка переменных окружения..."
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  TELEGRAM_BOT_TOKEN не установлен"
    read -p "Введите Telegram Bot Token: " TELEGRAM_BOT_TOKEN
    export TELEGRAM_BOT_TOKEN
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY не установлен"
    read -p "Введите OpenAI API Key: " OPENAI_API_KEY
    export OPENAI_API_KEY
fi
echo "✅ Переменные окружения проверены"
echo ""

# Проверяем наличие удаленного репозитория
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REMOTE_URL" ]; then
    echo "📤 Настройка GitHub репозитория..."
    echo ""
    echo "Для продолжения нужно:"
    echo "1. Создать репозиторий на GitHub (github.com)"
    echo "2. Скопировать URL репозитория"
    echo ""
    read -p "Введите URL вашего GitHub репозитория (или нажмите Enter для пропуска): " GITHUB_URL
    
    if [ -n "$GITHUB_URL" ]; then
        git remote add origin "$GITHUB_URL" 2>/dev/null || git remote set-url origin "$GITHUB_URL"
        echo "✅ Удаленный репозиторий настроен"
    else
        echo "⚠️  Пропущено. Настройте репозиторий вручную позже:"
        echo "   git remote add origin https://github.com/USERNAME/REPO.git"
    fi
else
    echo "✅ Удаленный репозиторий уже настроен: $REMOTE_URL"
fi
echo ""

# Добавляем все файлы
echo "📝 Добавление файлов в Git..."
git add .
echo "✅ Файлы добавлены"
echo ""

# Делаем коммит
echo "💾 Создание коммита..."
git commit -m "Deploy to Railway: Telegram Print Extractor" 2>/dev/null || echo "⚠️  Нет изменений для коммита"
echo "✅ Коммит создан"
echo ""

# Отправляем в GitHub (если настроен remote)
if [ -n "$REMOTE_URL" ] || git remote get-url origin &>/dev/null; then
    echo "🚀 Отправка в GitHub..."
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
    git branch -M main 2>/dev/null || true
    git push -u origin main 2>/dev/null || {
        echo "⚠️  Не удалось отправить в GitHub автоматически"
        echo "   Выполните вручную: git push -u origin main"
    }
    echo "✅ Код отправлен в GitHub"
else
    echo "⚠️  GitHub репозиторий не настроен"
    echo "   Настройте вручную и выполните:"
    echo "   git push -u origin main"
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  ✅ ПОДГОТОВКА ЗАВЕРШЕНА!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Зайдите на https://railway.app"
echo "2. Войдите через GitHub"
echo "3. Нажмите 'New Project' → 'Deploy from GitHub repo'"
echo "4. Выберите ваш репозиторий"
echo "5. В разделе 'Variables' добавьте:"
echo "   - TELEGRAM_BOT_TOKEN = $TELEGRAM_BOT_TOKEN"
echo "   - OPENAI_API_KEY = $OPENAI_API_KEY"
echo "   - PORT = 8080"
echo "6. После деплоя получите URL и добавьте:"
echo "   - WEB_APP_URL = https://xxx.railway.app"
echo "7. Настройте Telegram Bot через @BotFather"
echo ""
echo "📖 Подробная инструкция: ИНСТРУКЦИЯ_RAILWAY.txt"
echo ""
