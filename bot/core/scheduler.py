# bot/core/scheduler.py
"""
Планировщик для бота Пинки Пай.
Ежедневная отправка рецептов в 12:00.

Автор: MADAO81
Версия: 2.3
"""

import logging
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.config import Config
from bot.services.recipe_service import RecipeService
from bot.services.ai_service import get_pinkie_response

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
recipe_service = RecipeService()

DB_PATH = Config.DATA_DIR / "recipes.db"


def _get_connection():
    return sqlite3.connect(DB_PATH)


def _init_db():
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
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscriptions (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"📋 Чат {chat_id} добавлен для рассылки рецептов")


def remove_chat(chat_id: int):
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"📋 Чат {chat_id} удалён из рассылки")


def get_active_chats():
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscriptions")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


async def send_daily_recipe(app):
    active_chats = get_active_chats()

    if not active_chats:
        logger.info("📭 Нет активных чатов для рассылки рецептов")
        return

    logger.info(f"📅 Отправка ежедневного рецепта в {len(active_chats)} чатов...")

    try:
        # Получаем рецепт из БД
        recipe = recipe_service.get_random_recipe()

        if not recipe:
            logger.warning("⚠️ Не удалось получить рецепт")
            return

        # Формируем запрос к DeepSeek для «озвучивания» рецепта голосом Пинки
        prompt = (
            f"Перепиши этот рецепт в стиле Пинки Пай. Ты — Пинки Пай! "
            f"Расскажи рецепт так, как будто ты учишь друга готовить на своей кухне. "
            f"Говори энергично, весело, с шутками, с восклицаниями. "
            f"Добавь свои фирменные фразы: «Оки-доки-локи!», «добавь щепотку волшебства», «и вот так появилась Эквестрия!». "
            f"Используй эмодзи. Рецепт должен быть живым, как будто ты прыгаешь вокруг стола!\n\n"
            f"Название: {recipe['name']}\n"
            f"Ингредиенты: {recipe['ingredients']}\n"
            f"Инструкции: {recipe['instructions']}\n\n"
            f"Расскажи это по-своему, как Пинки Пай!"
        )

        # Получаем стилизованный рецепт от DeepSeek
        styled_recipe = await get_pinkie_response(prompt, mood_description="весёлое")

        if styled_recipe:
            message = f"🧁 *Рецепт от Пинки Пай!*\n\n{styled_recipe}"
        else:
            # fallback — если DeepSeek не ответил
            message = (
                f"🧁 *Вот что я испекла для тебя сегодня!*\n\n"
                f"*{recipe['name']}*\n\n"
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
    try:
        scheduler.shutdown()
        logger.info("⏹️ Планировщик остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке планировщика: {e}")
