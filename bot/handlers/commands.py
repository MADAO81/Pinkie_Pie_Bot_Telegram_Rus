# bot/handlers/commands.py
"""
Обработчики команд бота Пинки Пай:
/start, /help, /recipe, /joke, /song, /weather, /subscribe, /unsubscribe, /cleardata

Автор: MADAO81
Версия: 2.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.recipe_service import RecipeService
from bot.services.ai_service import get_pinkie_response
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.constants import VERSION
from bot.core.scheduler import add_chat, remove_chat
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
recipe_service = RecipeService()
weather_service = WeatherService()
context_manager = ContextManager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    mood, _ = await mood_system.determine_mood()
    mood_text = mood_system.get_mood_text(mood)
    mood_emoji = mood_system.get_mood_emoji(mood)

    text = (
        f"{mood_emoji} *Привет-привет! Я Пинки Пай!*\n\n"
        f"Я твоя весёлая пони-подружка! Обожаю вечеринки, сладости и улыбки! 😊\n\n"
        f"{mood_text}\n\n"
        f"📋 *Вот что я умею:*\n"
        f"/help — посмотреть все команды\n"
        f"/recipe — получить рецепт выпечки 🧁\n"
        f"/joke — услышать шутку 😄\n"
        f"/song — послушать песенку 🎵\n"
        f"/weather — узнать погоду 🌤️\n"
        f"/subscribe — подписаться на ежедневные рецепты 🧁\n"
        f"/unsubscribe — отписаться от рецептов 😢\n"
        f"/cleardata — удалить историю диалога 🗑️\n\n"
        f"🔒 *О данных:* Я сохраняю историю диалога только для поддержания беседы. "
        f"Данные не передаются третьим лицам. Напиши /cleardata, чтобы удалить всю историю.\n\n"
        f"Просто напиши мне что-нибудь, и мы поболтаем! 💖\n\n"
        f"🤖 *Версия:* {VERSION}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
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
        "/song — песенка от Пинки Пай 🎵\n"
        "/weather — погода в любом городе 🌤️\n"
        "/subscribe — подписаться на ежедневные рецепты 🧁\n"
        "/unsubscribe — отписаться от рецептов 😢\n"
        "/cleardata — удалить историю диалога 🗑️\n\n"
        "🔒 *О данных:* Я сохраняю историю диалога только для поддержания беседы. "
        "Данные не передаются третьим лицам. Напиши /cleardata, чтобы удалить всю историю.\n\n"
        "✨ *Особенности:*\n"
        "• Я работаю с 9:00 до 20:00 ежедневно\n"
        "• Если на улице дождь — могу немного погрустить 🌧️\n"
        "• Люблю комментировать сообщения и картинки с 20% вероятностью\n"
        "• Распознаю голосовые сообщения 🎤\n"
        "• Могу рассказать о погоде в любом городе\n"
        "• Всегда готова подбодрить и поддержать!\n\n"
        "💡 *Совет:* Просто напиши мне что-нибудь, и мы поболтаем!"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def recipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /recipe."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    status_message = await update.message.reply_text("🍳 Ищу для тебя вкусный рецепт... Подожди немного!")

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
            "😅 Ой-ой-ой! Не могу найти рецепт!\n"
            "Попробуй позже! 🍰"
        )


async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /joke."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    status_message = await update.message.reply_text("🤔 Дай-ка вспомнить хорошую шутку...")

    mood, _ = await mood_system.determine_mood()
    mood_desc = "грустное" if mood == "sad" else "весёлое"

    joke = await get_pinkie_response(
        "Расскажи короткую весёлую шутку. Без чёрного юмора, только добрые и смешные шутки. Не более 2-3 предложений.",
        mood_description=mood_desc
    )

    await status_message.delete()

    if joke:
        await update.message.reply_text(f"😄 {joke}")
    else:
        await update.message.reply_text("😅 Ой! Все шутки разбежались! Давай я лучше песенку спою? 🎵")


async def song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /song."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    status_message = await update.message.reply_text("🎵 Настраиваю голос... Ля-ля-ля!")

    mood, _ = await mood_system.determine_mood()
    mood_desc = "грустное" if mood == "sad" else "весёлое"

    song = await get_pinkie_response(
        "Придумай короткую весёлую песенку из 4-6 строк. Используй рифму и позитивный настрой. Песенка должна быть про дружбу, радость или сладости.",
        mood_description=mood_desc
    )

    await status_message.delete()

    if song:
        await update.message.reply_text(f"🎵 *Песенка от Пинки Пай:*\n\n{song}\n\n🎶 Ля-ля-ля! 🎶", parse_mode="Markdown")
    else:
        await update.message.reply_text("😅 Ой! Голос пропал! Наверное, я слишком много пела на вечеринках! 🎉")


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /weather.
    Показывает погоду в указанном городе или в Ворсино по умолчанию.
    """
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    args = context.args
    city = " ".join(args) if args else None

    status_message = await update.message.reply_text("🌤️ Смотрю в окно... Сейчас узнаю!")

    try:
        if city:
            weather = await weather_service.get_weather_by_city(city)
            if not weather:
                await status_message.edit_text(
                    f"😅 Не могу найти город '{city}'!\n"
                    "Проверь название или попробуй просто /weather для Ворсино 🌤️"
                )
                return
        else:
            weather = await weather_service.get_weather()

        if weather:
            weather_text = weather_service.get_weather_text(weather)
            
            details = (
                f"\n\n📊 *Подробнее:*\n"
                f"💧 Влажность: {weather.get('humidity', '?')}%\n"
                f"💨 Ветер: {weather.get('wind_speed', '?')} м/с\n"
                f"📈 Давление: {weather.get('pressure', '?')} мм рт. ст."
            )
            
            full_text = f"🌤️ *Погода*\n\n{weather_text}{details}"
            
            if not city:
                mood, _ = await mood_system.determine_mood()
                if mood == "sad":
                    full_text += "\n\n😔 Погодка сегодня грустная... Но мы всё равно найдём повод для улыбки!"
                else:
                    full_text += "\n\n🎈 Отличная погода для вечеринки! 🎉"
            
            await status_message.delete()
            await update.message.reply_text(full_text, parse_mode="Markdown")
        else:
            await status_message.edit_text(
                "😅 Ой-ой! Не могу узнать погоду!\n"
                "Попробуй позже! 🌧️"
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения погоды: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так при запросе погоды!\n"
            "Попробуй позже! 🌤️"
        )


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подписка на ежедневные рецепты."""
    chat_id = update.message.chat_id
    add_chat(chat_id)
    await update.message.reply_text(
        "🧁 *Ты подписался на ежедневные рецепты!*\n\n"
        "Каждый день в 12:00 я буду присылать тебе вкусный рецепт выпечки! 🎂\n\n"
        "Чтобы отписаться, напиши /unsubscribe 😢",
        parse_mode="Markdown"
    )


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отписка от ежедневных рецептов."""
    chat_id = update.message.chat_id
    remove_chat(chat_id)
    await update.message.reply_text(
        "😢 *Ты отписался от ежедневных рецептов!*\n\n"
        "Если захочешь вернуться — напиши /subscribe 🧁",
        parse_mode="Markdown"
    )


async def clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка истории диалога пользователя."""
    user_id = update.effective_user.id
    context_manager.clear_context(user_id)
    await update.message.reply_text(
        "🗑️ *Твоя история диалога удалена!*\n\n"
        "Теперь я ничего не помню о нашем разговоре. Но мы всегда можем начать заново! 😊🎈",
        parse_mode="Markdown"
    )
