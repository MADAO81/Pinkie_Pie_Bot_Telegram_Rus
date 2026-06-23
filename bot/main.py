# bot/main.py
"""
Главный модуль бота Пинки Пай.
Инициализация, настройка и запуск бота.

Автор: MADAO81
Версия: 2.0
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from bot.config import Config
from bot.handlers.commands import (
    start,
    help_command,
    recipe_command,
    joke_command,
    song_command,
    weather_command  # <-- ДОБАВЛЯЕМ
)
from bot.handlers.messages import handle_message
from bot.handlers.photos import handle_photo
from bot.handlers.voice import handle_voice
from bot.core.scheduler import start_scheduler
from bot.core.constants import VERSION

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("recipe", recipe_command))
    app.add_handler(CommandHandler("joke", joke_command))
    app.add_handler(CommandHandler("song", song_command))
    app.add_handler(CommandHandler("weather", weather_command))  # <-- ДОБАВЛЯЕМ

    # Регистрируем обработчики сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_voice))

    # Запускаем планировщик (ежедневная отправка рецептов)
    start_scheduler(app)

    # Запускаем бота
    logger.info("✅ Бот успешно запущен и готов к работе!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
