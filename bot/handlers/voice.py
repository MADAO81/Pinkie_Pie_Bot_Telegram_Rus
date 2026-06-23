# bot/handlers/voice.py
"""
Обработчик голосовых сообщений бота Пинки Пай.

Автор: MADAO81
Версия: 2.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.ai_service import transcribe_audio, get_pinkie_response
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка голосовых сообщений."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    if not mood_system.should_comment():
        return

    status_message = await update.message.reply_text("🎧 Слушаю тебя... Подожди немного!")

    try:
        user_id = update.effective_user.id

        voice = update.message.voice
        file = await voice.get_file()
        audio_data = await file.download_as_bytearray()

        transcript = await transcribe_audio(
            audio_data=bytes(audio_data),
            file_extension=".ogg"
        )

        if not transcript:
            await status_message.edit_text(
                "😅 Ой-ой! Я не смогла разобрать, что ты сказал(а)!\n"
                "Попробуй говорить чётче или напиши текстом! 💕"
            )
            return

        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        context_history = context_manager.get_context(user_id)

        response = await get_pinkie_response(
            user_message=transcript,
            mood_description=mood_desc,
            context_history=context_history
        )

        if not response:
            response = "😅 Ой-ой-ой! Что-то у меня мозги закипели!\nДавай попробуем ещё раз? 🎈"

        # Проверяем, спрашивает ли пользователь о погоде в голосовом
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер", "холодно", "тепло", "метео"]
        if any(keyword in transcript.lower() for keyword in weather_keywords):
            weather_text = weather_service.get_weather_text(weather)
            response += f"\n\n{weather_text}"

        await status_message.delete()

        reply_text = f"🎤 *Вы сказали:* _{transcript[:100]}..._\n\n{response}"

        if update.message.chat.type == "private":
            await update.message.reply_text(reply_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                reply_text,
                parse_mode="Markdown",
                reply_to_message_id=update.message.message_id
            )

        context_manager.save_context(user_id, transcript, response)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки голосового: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так при обработке голосового!\n"
            "Попробуй ещё раз или напиши текстом! 💕"
        )
