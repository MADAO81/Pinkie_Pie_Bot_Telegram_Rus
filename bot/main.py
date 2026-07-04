# bot/main.py
"""
Главный модуль бота Пинки Пай.
Инициализация, настройка и запуск бота.

Автор: MADAO81
Версия: 2.0
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from bot.config import Config
from bot.handlers.commands import (
    start,
    help_command,
    recipe_command,
    joke_command,
    song_command,
    weather_command,
    subscribe_command,
    unsubscribe_command,
    clear_data
)
from bot.handlers.admin import (
    add_recipe_command,
    list_recipes_command,
    del_recipe_command
)
from bot.handlers.messages import handle_message
from bot.handlers.photos import handle_photo
from bot.handlers.voice import handle_voice
from bot.core.scheduler import start_scheduler, add_chat
from bot.core.constants import VERSION

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Если включён DEBUG_MODE — поднимаем уровень логирования
if Config.DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("🐛 DEBUG_MODE включён")


def main():
    """
    Точка входа в приложение.

    Автор: MADAO81
    """
    logger.info(f"🎈 Запуск бота Пинки Пай (v{VERSION})...")
    logger.info(f"👤 Автор: MADAO81")

    # Проверяем наличие токена
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN не найден в .env файле!")
        return

    if not Config.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY не найден в .env файле!")
        return

    # Создаём приложение
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # === АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ПОДПИСОК ИЗ .env ===
    default_chats = os.getenv("DEFAULT_CHATS", "")
    if default_chats:
        for chat_id in default_chats.split(","):
            try:
                chat_id = int(chat_id.strip())
                add_chat(chat_id)
                logger.info(f"✅ Автоматически добавлен чат: {chat_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка добавления чата {chat_id}: {e}")

    # ===== 1. РЕГИСТРИРУЕМ ВСЕ КОМАНДЫ =====
    # Основные команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("recipe", recipe_command))
    app.add_handler(CommandHandler("joke", joke_command))
    app.add_handler(CommandHandler("song", song_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(CommandHandler("cleardata", clear_data))

    # Административные команды
    app.add_handler(CommandHandler("addrecipe", add_recipe_command))
    app.add_handler(CommandHandler("listrecipes", list_recipes_command))
    app.add_handler(CommandHandler("delrecipe", del_recipe_command))

    # ===== 2. РЕГИСТРИРУЕМ ОБРАБОТЧИКИ СООБЩЕНИЙ =====
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_voice))

    # Запускаем планировщик (ежедневная отправка рецептов)
    start_scheduler(app)

    # Запускаем бота
    logger.info("✅ Бот успешно запущен и готов к работе!")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
