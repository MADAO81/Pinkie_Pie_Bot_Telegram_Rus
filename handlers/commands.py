# bot/handlers/commands.py
"""
Обработчики команд бота Пинки Пай:
/start, /help, /recipe, /joke, /song

Автор: MADAO81
Версия: 2.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.recipe_service import RecipeService
from bot.services.ai_service import get_pinkie_response
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.constants import VERSION

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация сервисов
mood_system = MoodSystem()
recipe_service = RecipeService()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Приветствие и информация о боте.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # Определяем настроение
    mood, weather = await mood_system.determine_mood()
    mood_text = mood_system.get_mood_text(mood)
    mood_emoji = mood_system.get_mood_emoji(mood)

    # Формируем приветственное сообщение
    text = (
        f"{mood_emoji} *Привет-привет! Я Пинки Пай!*\n\n"
        f"Я твоя весёлая пони-подружка! Обожаю вечеринки, сладости и улыбки! 😊\n\n"
        f"{mood_text}\n\n"
        f"📋 *Вот что я умею:*\n"
        f"/help — посмотреть все команды\n"
        f"/recipe — получить рецепт выпечки 🧁\n"
        f"/joke — услышать шутку 😄\n"
        f"/song — послушать песенку 🎵\n\n"
        f"Просто напиши мне что-нибудь, и мы поболтаем! 💖\n\n"
        f"🤖 *Версия:* {VERSION}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help.
    Справка по командам.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    text = (
        "📖 *Команды Пинки Пай:*\n\n"
        "/start — начать общение 🎈\n"
        "/help — эта справка 📖\n"
        "/recipe — случайный рецепт выпечки 🧁\n"
        "/joke — весёлая шутка 😄\n"
        "/song — песенка от Пинки Пай 🎵\n\n"
        "✨ *Особенности:*\n"
        "• Я работаю с 9:00 до 20:00 ежедневно\n"
        "• Если на улице дождь — могу немного погрустить 🌧️\n"
        "• Люблю комментировать сообщения и картинки с 20% вероятностью\n"
        "• Распознаю голосовые сообщения 🎤\n"
        "• Всегда готова подбодрить и поддержать!\n\n"
        "💡 *Совет:* Просто напиши мне что-нибудь, и мы поболтаем!"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def recipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /recipe.
    Получение случайного рецепта.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # Отправляем статус
    status_message = await update.message.reply_text(
        "🍳 Ищу для тебя вкусный рецепт... Подожди немного!"
    )

    # Получаем рецепт
    recipe = await recipe_service.get_random_recipe()

    if recipe:
        text = (
            f"🧁 *Вот что я нашла для тебя!*\n\n"
            f"*{recipe['title']}*\n\n"
            f"📝 *Ингредиенты:*\n{recipe['ingredients']}\n\n"
            f"👩‍🍳 *Приготовление:*\n{recipe['instructions']}\n\n"
            f"Приятного аппетита! 🎂 Не забудь позвать меня на чай! ☕"
        )
        await status_message.delete()
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await status_message.edit_text(
            "😅 Ой-ой-ой! Не могу найти рецепт на andychef.ru!\n"
            "Попробуй позже или загляни на сайт сам! 🍰"
        )


async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /joke.
    Рассказать шутку.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # Отправляем статус
    status_message = await update.message.reply_text("🤔 Дай-ка вспомнить хорошую шутку...")

    # Определяем настроение
    mood, _ = await mood_system.determine_mood()
    mood_desc = "грустное" if mood == "sad" else "весёлое"

    # Генерируем шутку
    joke = await get_pinkie_response(
        "Расскажи короткую весёлую шутку. Без чёрного юмора, только добрые и смешные шутки. Не более 2-3 предложений.",
        mood_description=mood_desc
    )

    await status_message.delete()

    if joke:
        await update.message.reply_text(f"😄 {joke}")
    else:
        await update.message.reply_text(
            "😅 Ой! Все шутки разбежались! Давай я лучше песенку спою? 🎵"
        )


async def song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /song.
    Спеть песенку.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # Отправляем статус
    status_message = await update.message.reply_text("🎵 Настраиваю голос... Ля-ля-ля!")

    # Определяем настроение
    mood, _ = await mood_system.determine_mood()
    mood_desc = "грустное" if mood == "sad" else "весёлое"

    # Генерируем песенку
    song = await get_pinkie_response(
        "Придумай короткую весёлую песенку из 4-6 строк. Используй рифму и позитивный настрой. Песенка должна быть про дружбу, радость или сладости.",
        mood_description=mood_desc
    )

    await status_message.delete()

    if song:
        await update.message.reply_text(f"🎵 *Песенка от Пинки Пай:*\n\n{song}\n\n🎶 Ля-ля-ля! 🎶", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "😅 Ой! Голос пропал! Наверное, я слишком много пела на вечеринках! 🎉"
        )
