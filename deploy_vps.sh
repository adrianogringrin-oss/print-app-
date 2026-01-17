#!/bin/bash
# Скрипт для развертывания на VPS

set -e

echo "🚀 Развертывание на VPS"
echo ""

# Проверяем, что скрипт запущен от root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите скрипт от root: sudo $0"
    exit 1
fi

# Запрашиваем данные
read -p "Введите IP адрес сервера: " SERVER_IP
read -p "Введите Telegram Bot Token: " TELEGRAM_BOT_TOKEN
read -p "Введите OpenAI API Key: " OPENAI_API_KEY
read -p "Введите домен (или оставьте пустым для IP): " DOMAIN

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Токен и ключ обязательны!"
    exit 1
fi

APP_DIR="/opt/telegram-print-extractor"
WEB_APP_URL="${DOMAIN:-http://$SERVER_IP}"

echo ""
echo "📦 Установка зависимостей..."
apt update
apt install -y python3 python3-pip git nginx certbot python3-certbot-nginx

echo ""
echo "📥 Клонирование репозитория..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull
else
    read -p "Введите URL репозитория GitHub: " REPO_URL
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

echo ""
echo "📚 Установка Python зависимостей..."
pip3 install -r requirements_telegram.txt

echo ""
echo "⚙️  Создание .env файла..."
cat > "$APP_DIR/.env" <<EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
OPENAI_API_KEY=$OPENAI_API_KEY
WEB_APP_URL=$WEB_APP_URL
PORT=8080
EOF
chmod 600 "$APP_DIR/.env"

echo ""
echo "🔧 Создание systemd сервисов..."

# Web App сервис
cat > /etc/systemd/system/telegram-webapp.service <<EOF
[Unit]
Description=Telegram Web App Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/bin/python3 $APP_DIR/TELEGRAM_WEBAPP_SERVER.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Bot сервис
cat > /etc/systemd/system/telegram-bot.service <<EOF
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/bin/python3 $APP_DIR/TELEGRAM_BOT_SERVER.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🚀 Запуск сервисов..."
systemctl daemon-reload
systemctl enable telegram-webapp telegram-bot
systemctl start telegram-webapp telegram-bot

echo ""
echo "⏳ Ожидание запуска сервисов..."
sleep 5

# Проверка статуса
if systemctl is-active --quiet telegram-webapp && systemctl is-active --quiet telegram-bot; then
    echo "✅ Сервисы запущены успешно!"
else
    echo "⚠️  Проблемы с запуском сервисов. Проверьте логи:"
    echo "   journalctl -u telegram-webapp -n 50"
    echo "   journalctl -u telegram-bot -n 50"
fi

# Настройка Nginx
if [ -n "$DOMAIN" ]; then
    echo ""
    echo "🌐 Настройка Nginx для домена: $DOMAIN"
    
    cat > /etc/nginx/sites-available/telegram-app <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/telegram-app /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    nginx -t
    systemctl restart nginx
    
    echo ""
    echo "🔒 Настройка SSL сертификата..."
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" || true
    
    # Обновляем WEB_APP_URL на HTTPS
    sed -i "s|WEB_APP_URL=.*|WEB_APP_URL=https://$DOMAIN|" "$APP_DIR/.env"
    systemctl restart telegram-webapp telegram-bot
    
    FINAL_URL="https://$DOMAIN"
else
    echo ""
    echo "⚠️  Домен не указан. Настройте Nginx вручную для HTTPS."
    FINAL_URL="http://$SERVER_IP"
fi

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📊 Статус сервисов:"
systemctl status telegram-webapp --no-pager -l
echo ""
systemctl status telegram-bot --no-pager -l
echo ""
echo "📱 URL приложения: $FINAL_URL"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Откройте @BotFather в Telegram"
echo "   2. Отправьте /setmenubutton"
echo "   3. Выберите вашего бота"
echo "   4. Введите URL: $FINAL_URL"
echo ""
echo "🔍 Полезные команды:"
echo "   systemctl status telegram-webapp"
echo "   systemctl status telegram-bot"
echo "   journalctl -u telegram-webapp -f"
echo "   journalctl -u telegram-bot -f"
