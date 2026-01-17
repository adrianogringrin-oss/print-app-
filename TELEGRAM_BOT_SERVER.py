#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Mini App для извлечения принтов - СЕРВЕРНАЯ ВЕРСИЯ
Бот для обработки команд и загрузки изображений
"""

import os
import sys
import json
import logging
from pathlib import Path
import tempfile

# Импорты без macOS-специфичных путей
from PIL import Image

# Telegram Bot API
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False
    print("❌ python-telegram-bot не установлен. Установите: pip install python-telegram-bot")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'http://localhost:8080')

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
        "🎨 **Привет! Я бот для извлечения принтов и надписей.**\n\n"
        "📸 Отправьте изображение или нажмите кнопку, чтобы открыть редактор!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


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
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото"""
    user_id = str(update.effective_user.id)
    photo = update.message.photo[-1]  # Берем самое большое фото
    
    try:
        file = await context.bot.get_file(photo.file_id)
        temp_path = temp_dir / f"{user_id}_{photo.file_id}.jpg"
        
        await file.download_to_drive(temp_path)
        image = Image.open(temp_path)
        
        user_sessions[user_id] = {
            'image_path': str(temp_path),
            'image': image,
            'file_id': photo.file_id
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
        logger.error(f"Ошибка обработки фото: {e}")
        await update.message.reply_text("❌ Ошибка при обработке изображения. Попробуйте еще раз.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка документов (изображений)"""
    user_id = str(update.effective_user.id)
    document = update.message.document
    
    if not document.mime_type or not document.mime_type.startswith('image/'):
        await update.message.reply_text("❌ Пожалуйста, отправьте изображение (PNG, JPG, etc.)")
        return
    
    try:
        file = await context.bot.get_file(document.file_id)
        temp_path = temp_dir / f"{user_id}_{document.file_id}.{document.file_name.split('.')[-1] if document.file_name else 'jpg'}"
        
        await file.download_to_drive(temp_path)
        image = Image.open(temp_path)
        
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


def get_user_image(user_id):
    """Получить изображение пользователя"""
    return user_sessions.get(user_id)


def main():
    """Главная функция"""
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        sys.exit(1)
    
    if not HAS_TELEGRAM:
        logger.error("❌ python-telegram-bot не установлен!")
        sys.exit(1)
    
    logger.info("🤖 Бот запущен...")
    logger.info(f"🌐 Web App URL: {WEB_APP_URL}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
