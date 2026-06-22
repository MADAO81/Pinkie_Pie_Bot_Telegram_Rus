# bot/core/scheduler.py
"""
Планировщик задач для бота Пинки Пай.
Ежедневная отправка рецептов в 12:00.

Автор: MADAO81
Версия: 2.0
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from bot.config import Config
from bot.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)

# Глобальный планировщик
scheduler = AsyncIOScheduler()
recipe_service = RecipeService()


async def send_daily_recipe(app):
    """
    Отправка ежедневного рецепта всем активным чатам.

    Args:
        app: Экземпляр приложения telegram-bot
    """
    logger.info("📅 Отправка ежедневного рецепта...")

    try:
        # Получаем рецепт
        recipe = await recipe_service.get_random_recipe()

        if not recipe:
            logger.warning("⚠️ Не удалось получить рецепт")
            return

        # Формируем сообщение с рецептом
        message = (
            f"🧁 *Вот что я испекла для тебя сегодня!*\n\n"
            f"*{recipe['title']}*\n\n"
            f"📝 *Ингредиенты:*\n{recipe['ingredients']}\n\n"
            f"👩‍🍳 *Приготовление:*\n{recipe['instructions']}\n\n"
            f"Приятного аппетита! 🎂 Не забудь позвать меня на чай! ☕"
        )

        # Здесь нужно отправлять рецепт всем активным чатам
        # Пока просто логируем
        logger.info(f"✅ Рецепт получен: {recipe['title']}")

        # TODO: Реализовать отправку в активные чаты
        # Для этого нужно хранить список chat_id в БД

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке рецепта: {e}")


def start_scheduler(app):
    """
    Запуск планировщика.

    Args:
        app: Экземпляр приложения telegram-bot
    """
    try:
        # Настраиваем расписание: каждый день в указанное время
        hour, minute = map(int, Config.RECIPE_SEND_TIME.split(':'))

        scheduler.add_job(
            send_daily_recipe,
            CronTrigger(hour=hour, minute=minute),
            args=[app],
            id='daily_recipe',
            replace_existing=True
        )

        scheduler.start()
        logger.info(f"✅ Планировщик запущен. Ежедневная отправка рецептов в {Config.RECIPE_SEND_TIME}")

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске планировщика: {e}")


def stop_scheduler():
    """Остановка планировщика."""
    try:
        scheduler.shutdown()
        logger.info("⏹️ Планировщик остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке планировщика: {e}")
