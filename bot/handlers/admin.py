# bot/handlers/admin.py
"""
Административные команды для бота Пинки Пай.
Добавление рецептов через Telegram.

Автор: MADAO81
Версия: 1.0
"""

import logging
import sqlite3
import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config
from bot.utils.time_utils import is_working_hours

logger = logging.getLogger(__name__)

# ID администратора (задаётся в .env)
ADMIN_ID = int(Config.ADMIN_ID) if hasattr(Config, 'ADMIN_ID') and Config.ADMIN_ID else None

# Путь к БД рецептов
DB_PATH = Config.DATA_DIR / "recipes.db"


async def add_recipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /addrecipe — добавление нового рецепта.
    Доступна только администратору.
    Формат: /addrecipe Название | Ингредиенты | Инструкции | Категория
    """
    # Проверяем, что пользователь — администратор
    if ADMIN_ID is None:
        await update.message.reply_text(
            "❌ Администратор не настроен!\n"
            "Добавьте ADMIN_ID=ваш_id в файл .env"
        )
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды!")
        return

    # Проверяем рабочее время
    if not is_working_hours():
        await update.message.reply_text("⏰ Бот работает только с 9:00 до 20:00")
        return

    # Получаем аргументы команды
    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *Как добавить рецепт:*\n\n"
            "`/addrecipe Название | Ингредиенты | Инструкции | Категория`\n\n"
            "📌 *Пример:*\n"
            "`/addrecipe Шоколадный торт | Мука 200г, Сахар 150г, Какао 50г, Яйца 3шт | Смешать сухие ингредиенты, добавить яйца, выпекать 40 минут при 180°C | торты`\n\n"
            "📂 *Категории:* торты, пирожные, печенье, кексы, пироги, десерты, другое",
            parse_mode="Markdown"
        )
        return

    # Собираем всё сообщение
    full_text = " ".join(args)

    # Разделяем по |
    parts = full_text.split("|")

    if len(parts) < 3:
        await update.message.reply_text(
            "❌ Неверный формат! Используйте разделитель `|`.\n"
            "Пример: `/addrecipe Название | Ингредиенты | Инструкции | Категория`",
            parse_mode="Markdown"
        )
        return

    title = parts[0].strip()
    ingredients = parts[1].strip()
    instructions = parts[2].strip()
    category = parts[3].strip() if len(parts) > 3 else "другое"

    # Проверяем, что все поля заполнены
    if not title or not ingredients or not instructions:
        await update.message.reply_text(
            "❌ Все поля должны быть заполнены!\n"
            "Формат: `/addrecipe Название | Ингредиенты | Инструкции | Категория`",
            parse_mode="Markdown"
        )
        return

    # Сохраняем в БД
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO recipes (title, ingredients, instructions, category, source)
            VALUES (?, ?, ?, ?, ?)
        """, (title, ingredients, instructions, category, 'админ'))

        conn.commit()
        conn.close()

        # Отправляем подтверждение
        await update.message.reply_text(
            f"✅ *Рецепт успешно добавлен!*\n\n"
            f"📌 *Название:* {title}\n"
            f"📂 *Категория:* {category}\n"
            f"📝 *Ингредиенты:* {ingredients[:100]}{'...' if len(ingredients) > 100 else ''}\n"
            f"👩‍🍳 *Инструкции:* {instructions[:100]}{'...' if len(instructions) > 100 else ''}\n\n"
            f"Теперь рецепт доступен по команде /recipe! 🎂",
            parse_mode="Markdown"
        )

        logger.info(f"✅ Администратор добавил рецепт: {title}")

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении рецепта: {e}")
        await update.message.reply_text(f"❌ Ошибка при добавлении рецепта: {e}")


async def list_recipes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /listrecipes — показать последние 20 рецептов (только для админа).
    """
    if ADMIN_ID is None:
        await update.message.reply_text("❌ Администратор не настроен!")
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category FROM recipes ORDER BY id DESC LIMIT 20")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("📭 В базе нет рецептов.")
            return

        text = "📋 *Последние 20 рецептов:*\n\n"
        for row in rows:
            text += f"`{row[0]}`. {row[1]} — *{row[2]}*\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка рецептов: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def del_recipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /delrecipe [id] — удалить рецепт по ID (только для админа).
    """
    if ADMIN_ID is None:
        await update.message.reply_text("❌ Администратор не настроен!")
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды!")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *Как удалить рецепт:*\n\n"
            "`/delrecipe ID`\n\n"
            "Чтобы узнать ID, используйте команду /listrecipes",
            parse_mode="Markdown"
        )
        return

    try:
        recipe_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Проверяем, существует ли рецепт
        cursor.execute("SELECT title FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text(f"❌ Рецепт с ID {recipe_id} не найден!")
            conn.close()
            return

        title = row[0]

        # Удаляем
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ *Рецепт удалён!*\n\n"
            f"📌 *Название:* {title}\n"
            f"🆔 *ID:* {recipe_id}",
            parse_mode="Markdown"
        )

        logger.info(f"✅ Администратор удалил рецепт: {title} (ID: {recipe_id})")

    except Exception as e:
        logger.error(f"❌ Ошибка при удалении рецепта: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")
