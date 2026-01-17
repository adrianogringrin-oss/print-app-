#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Mini App для извлечения принтов
Бот для обработки команд и загрузки изображений
"""

import os
import sys
import json
import logging
from pathlib import Path
import tempfile

# Добавляем пути к библиотекам
user_site_314 = os.path.expanduser('~/Library/Python/3.14/lib/python/site-packages')
if os.path.exists(user_site_314) and user_site_314 not in sys.path:
    sys.path.insert(0, user_site_314)

from PIL import Image

# Telegram Bot API
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False
    print("❌ python-telegram-bot не установлен. Установите: pip3 install python-telegram-bot")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'http://localhost:8080')  # URL вашего веб-приложения

# Глобальное хранилище (в продакшене используйте Redis или БД)
user_sessions = {}
temp_dir = Path(tempfile.gettempdir()) / 'telegram_print_extractor'
temp_dir.mkdir(exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton(
            "🎨 Открыть приложение",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в приложение для извлечения принтов!\n\n"
        "📸 Загрузите изображение и выберите область для извлечения\n"
        "🤖 Или используйте ИИ для автоматического определения\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение:",
        reply_markup=reply_markup
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженного фото"""
    photo = update.message.photo[-1]  # Берем фото максимального качества
    
    # Скачиваем фото
    file = await context.bot.get_file(photo.file_id)
    
    # Сохраняем временно
    user_id = update.effective_user.id
    temp_path = temp_dir / f"{user_id}_{photo.file_id}.jpg"
    await file.download_to_drive(temp_path)
    
    # Открываем изображение
    try:
        image = Image.open(temp_path)
        
        # Сохраняем в сессию пользователя
        user_sessions[user_id] = {
            'image_path': str(temp_path),
            'image': image,
            'file_id': photo.file_id
        }
        
        # Отправляем кнопку для открытия веб-приложения
        keyboard = [
            [InlineKeyboardButton(
                "🎨 Обработать изображение",
                web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Изображение загружено!\n"
            f"📐 Размер: {image.size[0]}x{image.size[1]} пикселей\n\n"
            f"Нажмите кнопку, чтобы открыть редактор:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await update.message.reply_text("❌ Ошибка при обработке изображения. Попробуйте еще раз.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженного документа (изображения)"""
    document = update.message.document
    
    # Проверяем, что это изображение
    if not document.mime_type or not document.mime_type.startswith('image/'):
        await update.message.reply_text("❌ Пожалуйста, загрузите изображение (JPG, PNG и т.д.)")
        return
    
    # Скачиваем файл
    file = await context.bot.get_file(document.file_id)
    
    user_id = update.effective_user.id
    # Определяем расширение
    ext = document.file_name.split('.')[-1] if document.file_name else 'jpg'
    temp_path = temp_dir / f"{user_id}_{document.file_id}.{ext}"
    await file.download_to_drive(temp_path)
    
    # Открываем изображение
    try:
        image = Image.open(temp_path)
        
        # Сохраняем в сессию
        user_sessions[user_id] = {
            'image_path': str(temp_path),
            'image': image,
            'file_id': document.file_id
        }
        
        keyboard = [
            [InlineKeyboardButton(
                "🎨 Обработать изображение",
                web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Изображение загружено!\n"
            f"📐 Размер: {image.size[0]}x{image.size[1]} пикселей\n\n"
            f"Нажмите кнопку, чтобы открыть редактор:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Ошибка обработки документа: {e}")
        await update.message.reply_text("❌ Ошибка при обработке изображения. Попробуйте еще раз.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 **Инструкция по использованию:**

1️⃣ **Загрузите изображение:**
   - Отправьте фото в чат
   - Или отправьте файл (PNG, JPG)

2️⃣ **Откройте приложение:**
   - Нажмите кнопку "Обработать изображение"
   - Или используйте команду /start

3️⃣ **Выберите режим:**
   - 🖱️ **Ручной выбор** - выделите область мышью
   - 🤖 **ИИ режим** - опишите что нужно извлечь

4️⃣ **Получите результат:**
   - Скачайте готовое изображение с прозрачным фоном

💡 **Советы:**
- Для текста используйте ИИ: "извлеки весь текст"
- Для объектов: "извлеки автомобиль", "извлеки логотип"
- Результат будет в формате PNG с прозрачным фоном
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


def get_user_image(user_id):
    """Получить изображение пользователя из сессии"""
    return user_sessions.get(user_id)


def main():
    """Запуск бота"""
    if not HAS_TELEGRAM:
        print("❌ Установите python-telegram-bot: pip3 install python-telegram-bot")
        return
    
    if not BOT_TOKEN:
        print("❌ Установите переменную окружения TELEGRAM_BOT_TOKEN")
        print("   Получите токен у @BotFather в Telegram")
        print("   Пример: export TELEGRAM_BOT_TOKEN='ваш_токен'")
        return
    
    if not WEB_APP_URL or WEB_APP_URL == 'http://localhost:8080':
        print("⚠️  ВНИМАНИЕ: WEB_APP_URL не настроен!")
        print("   Установите переменную окружения WEB_APP_URL")
        print("   Пример: export WEB_APP_URL='https://your-domain.com'")
        print("   Для тестирования можно использовать ngrok")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    
    # Запускаем бота
    logger.info("🤖 Бот запущен...")
    logger.info(f"🌐 Web App URL: {WEB_APP_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
