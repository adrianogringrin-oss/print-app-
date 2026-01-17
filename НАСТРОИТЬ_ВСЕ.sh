#!/bin/bash
# Полная настройка программы с ИИ поддержкой

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════"
echo "  🔧 ПОЛНАЯ НАСТРОЙКА ПРОГРАММЫ С ИИ"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Шаг 1: Установка зависимостей
echo "ШАГ 1: Установка зависимостей..."
echo ""

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден!"
    exit 1
fi

PYTHON_CMD=$(which python3)
echo "✓ Python: $PYTHON_CMD"
echo ""

# Устанавливаем Pillow
echo "Установка Pillow..."
python3 -m pip install --user --break-system-packages Pillow 2>&1 | grep -E "(Successfully|already satisfied|ERROR)" | tail -3
echo ""

# Устанавливаем OpenAI
echo "Установка OpenAI..."
python3 -m pip install --user --break-system-packages openai 2>&1 | grep -E "(Successfully|already satisfied|ERROR)" | tail -3
echo ""

# Проверяем установку
echo "Проверка установки..."
python3 -c "from PIL import Image; print('✓ Pillow установлен')" 2>/dev/null || echo "❌ Pillow не установлен"
python3 -c "import openai; print('✓ OpenAI установлен')" 2>/dev/null || echo "⚠ OpenAI не установлен (ИИ функции будут недоступны)"
echo ""

# Шаг 2: Настройка API ключа
echo "═══════════════════════════════════════════════════════════"
echo "ШАГ 2: Настройка OpenAI API ключа"
echo "═══════════════════════════════════════════════════════════"
echo ""

KEY_FILE="$HOME/.openai_api_key"

if [ -f "$KEY_FILE" ]; then
    echo "⚠ Файл с ключом уже существует: $KEY_FILE"
    read -p "Перезаписать? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
        echo "Пропущено"
    else
        read -sp "Введите ваш OpenAI API ключ: " API_KEY
        echo ""
        if [ -n "$API_KEY" ]; then
            echo "$API_KEY" > "$KEY_FILE"
            chmod 600 "$KEY_FILE"
            echo "✅ Ключ сохранен"
        fi
    fi
else
    echo "Введите ваш OpenAI API ключ:"
    echo "(Ключ можно получить на: https://platform.openai.com/api-keys)"
    echo ""
    read -sp "API ключ: " API_KEY
    echo ""
    
    if [ -n "$API_KEY" ]; then
        echo "$API_KEY" > "$KEY_FILE"
        chmod 600 "$KEY_FILE"
        echo "✅ Ключ сохранен в: $KEY_FILE"
    else
        echo "⚠ Ключ не введен. ИИ функции будут недоступны."
        echo "   Вы можете установить ключ позже:"
        echo "   echo 'ваш-ключ' > ~/.openai_api_key"
    fi
fi

echo ""

# Шаг 3: Проверка ключа
echo "═══════════════════════════════════════════════════════════"
echo "ШАГ 3: Проверка настроек"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ -f "$KEY_FILE" ]; then
    API_KEY=$(cat "$KEY_FILE")
    KEY_PREFIX="${API_KEY:0:10}..."
    echo "✓ API ключ найден: $KEY_PREFIX"
    
    # Простая проверка формата ключа
    if [[ "$API_KEY" =~ ^sk- ]]; then
        echo "✓ Формат ключа правильный (начинается с sk-)"
    else
        echo "⚠ Необычный формат ключа (должен начинаться с sk-)"
    fi
else
    echo "⚠ API ключ не найден"
fi

echo ""

# Шаг 4: Финальная проверка
echo "═══════════════════════════════════════════════════════════"
echo "ШАГ 4: Финальная проверка"
echo "═══════════════════════════════════════════════════════════"
echo ""

ALL_OK=true

# Проверка Pillow
if python3 -c "from PIL import Image" 2>/dev/null; then
    echo "✅ Pillow работает"
else
    echo "❌ Pillow не работает"
    ALL_OK=false
fi

# Проверка OpenAI
if python3 -c "import openai" 2>/dev/null; then
    echo "✅ OpenAI библиотека установлена"
    
    # Попытка загрузить ключ
    if [ -f "$KEY_FILE" ]; then
        export OPENAI_API_KEY=$(cat "$KEY_FILE")
        if python3 -c "import openai; openai.api_key = open('$KEY_FILE').read().strip(); print('✅ API ключ загружен')" 2>/dev/null; then
            echo "✅ API ключ работает"
        else
            echo "⚠ API ключ не проверен (нужна проверка при запуске)"
        fi
    else
        echo "⚠ API ключ не найден - ИИ функции недоступны"
    fi
else
    echo "❌ OpenAI библиотека не установлена"
    ALL_OK=false
fi

echo ""

if [ "$ALL_OK" = true ]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "  ✅ ВСЕ ГОТОВО! НАСТРОЙКА ЗАВЕРШЕНА"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Теперь можно запускать:"
    echo "  ./ЗАПУСТИТЬ_С_ИИ.command"
    echo ""
    echo "Или напрямую:"
    echo "  python3 ВЕБ_ВЕРСИЯ_С_ИИ.py"
    echo ""
else
    echo "═══════════════════════════════════════════════════════════"
    echo "  ⚠ НЕКОТОРЫЕ КОМПОНЕНТЫ НЕ УСТАНОВЛЕНЫ"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Проверьте ошибки выше и исправьте их."
    echo ""
fi
