#!/bin/bash
# Скрипт для создания .app bundle для macOS

cd "$(dirname "$0")"

APP_NAME="ИзвлечениеПринтов"
APP_DIR="${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

echo "Создание .app bundle для macOS..."
echo ""

# Удаляем старый .app если есть
if [ -d "$APP_DIR" ]; then
    echo "Удаление старого .app..."
    rm -rf "$APP_DIR"
fi

# Создаем структуру .app
echo "Создание структуры .app..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Создаем Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.printextractor.app</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF

# Создаем скрипт запуска
cat > "${MACOS_DIR}/${APP_NAME}" << 'SCRIPT'
#!/bin/bash
# Скрипт запуска приложения

# Получаем путь к .app
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP_DIR/Contents/Resources"

# Определяем Python
PYTHON_CMD=""

# Пробуем системный Python (обычно имеет tkinter)
if [ -f "/usr/bin/python3" ]; then
    /usr/bin/python3 -c "import tkinter" 2>/dev/null
    if [ $? -eq 0 ]; then
        PYTHON_CMD="/usr/bin/python3"
    fi
fi

# Если системный не работает, пробуем Homebrew
if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD=$(which python3)
fi

# Запускаем приложение
exec "$PYTHON_CMD" "GUI_РАБОТАЮЩАЯ.py"
SCRIPT

chmod +x "${MACOS_DIR}/${APP_NAME}"

# Копируем Python скрипт в Resources
echo "Копирование файлов..."
cp "GUI_РАБОТАЮЩАЯ.py" "$RESOURCES_DIR/"

# Создаем иконку (простая замена)
# Можно заменить на свою иконку позже
echo "Создание структуры завершено"
echo ""
echo "✅ .app bundle создан: ${APP_DIR}"
echo ""
echo "Теперь можно:"
echo "1. Дважды кликнуть на ${APP_DIR} для запуска"
echo "2. Перетащить в Applications для установки"
echo ""
echo "Примечание: Для работы нужны зависимости:"
echo "  - Pillow, numpy, opencv-python"
echo "  - tkinter (обычно есть в системном Python)"
