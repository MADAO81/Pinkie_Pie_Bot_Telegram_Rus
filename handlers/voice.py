# bot/handlers/voice.py
"""
Обработчик голосовых сообщений бота Пинки Пай.
Распознавание речи через OpenAI Whisper.

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

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация сервисов
mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка голосовых сообщений.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # Проверяем, нужно ли комментировать (20% вероятности)
    if not mood_system.should_comment():
        return

    # Отправляем статус
    status_message = await update.message.reply_text("🎧 Слушаю тебя... Подожди немного!")

    try:
        user_id = update.effective_user.id

        # Получаем голосовое сообщение
        voice = update.message.voice
        file = await voice.get_file()

        # Скачиваем аудио
        audio_data = await file.download_as_bytearray()

        # Транскрибируем через Whisper
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

        # Определяем настроение
        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        # Получаем контекст диалога
        context_history = context_manager.get_context(user_id)

        # Генерируем ответ
        response = await get_pinkie_response(
            user_message=transcript,
            mood_description=mood_desc,
            context_history=context_history
        )

        if not response:
            response = (
                "😅 Ой-ой-ой! Что-то у меня мозги закипели!\n"
                "Давай попробуем ещё раз? 🎈"
            )

        # Добавляем погоду
        weather_text = weather_service.get_weather_text(weather)
        response += f"\n\n{weather_text}"

        # Удаляем статус и отправляем ответ
        await status_message.delete()

        # Отправляем ответ с транскриптом
        reply_text = (
            f"🎤 *Вы сказали:* _{transcript[:100]}..._\n\n"
            f"{response}"
        )

        if update.message.chat.type == "private":
            await update.message.reply_text(reply_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                reply_text,
                parse_mode="Markdown",
                reply_to_message_id=update.message.message_id
            )

        # Сохраняем контекст
        context_manager.save_context(user_id, transcript, response)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки голосового: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так при обработке голосового!\n"
            "Попробуй ещё раз или напиши текстом! 💕"
        )
