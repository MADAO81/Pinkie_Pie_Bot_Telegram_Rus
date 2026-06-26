# bot/core/scheduler.py
"""
Планировщик задач для бота Пинки Пай.
Ежедневная отправка рецептов в 12:00.

Автор: MADAO81
Версия: 2.1 (с сохранением подписок в БД)
"""

import logging
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.config import Config
from bot.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
recipe_service = RecipeService()

# Путь к БД
DB_PATH = Config.DATA_DIR / "recipes.db"


def _get_connection():
    """Возвращает соединение с БД."""
    return sqlite3.connect(DB_PATH)


def _init_db():
    """Создаёт таблицу подписок, если её нет."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            chat_id INTEGER PRIMARY KEY,
            subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_chat(chat_id: int):
    """Добавляет чат для ежедневной рассылки."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscriptions (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"📋 Чат {chat_id} добавлен для рассылки рецептов")


def remove_chat(chat_id: int):
    """Удаляет чат из рассылки."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"📋 Чат {chat_id} удалён из рассылки")


def get_active_chats():
    """Возвращает список активных чатов из БД."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscriptions")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


async def send_daily_recipe(app):
    """
    Отправка ежедневного рецепта всем активным чатам.
    """
    active_chats = get_active_chats()

    if not active_chats:
        logger.info("📭 Нет активных чатов для рассылки рецептов")
        return

    logger.info(f"📅 Отправка ежедневного рецепта в {len(active_chats)} чатов...")

    try:
        recipe = await recipe_service.get_random_recipe()

        if not recipe:
            logger.warning("⚠️ Не удалось получить рецепт")
            return

        message = (
            f"🧁 *Вот что я испекла для тебя сегодня!*\n\n"
            f"*{recipe['title']}*\n\n"
            f"📝 *Ингредиенты:*\n{recipe['ingredients']}\n\n"
            f"👩‍🍳 *Приготовление:*\n{recipe['instructions']}\n\n"
            f"Приятного аппетита! 🎂 Не забудь позвать меня на чай! ☕"
        )

        for chat_id in active_chats:
            try:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Рецепт отправлен в чат {chat_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки в чат {chat_id}: {e}")
                if "bot was blocked" in str(e) or "chat not found" in str(e):
                    remove_chat(chat_id)

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке рецепта: {e}")


def start_scheduler(app):
    """Запуск планировщика."""
    try:
        _init_db()
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
