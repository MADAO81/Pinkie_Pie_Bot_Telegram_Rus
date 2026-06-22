# bot/handlers/photos.py
"""
Обработчик фотографий бота Пинки Пай.
Анализ изображений через OpenAI Vision API.

Автор: MADAO81
Версия: 2.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.ai_service import analyze_image
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours
from bot.core.context_manager import ContextManager

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация сервисов
mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка фотографий.

    Args:
        update (Update): Объект обновления
        context (ContextTypes.DEFAULT_TYPE): Контекст
    """
    # Проверяем рабочее время
    if not is_working_hours():
        return

    # Проверяем, нужно ли комментировать (20% вероятности)
    if not mood_system.should_comment():
        return

    # Отправляем статус
    status_message = await update.message.reply_text("🖼️ Смотрю на картинку... Сейчас что-то придумаю!")

    try:
        user_id = update.effective_user.id
        user_message = update.message.caption or "Красивая картинка!"

        # Получаем фото в максимальном качестве
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()

        # Определяем настроение
        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        # Анализируем изображение через Vision API
        response = await analyze_image(
            image_data=bytes(image_data),
            user_message=user_message,
            mood_description=mood_desc
        )

        if not response:
            response = "🖼️ Ой, какая красивая картинка! Жаль, что у меня сейчас глаза разбегаются от такого великолепия! 😄"

        # Добавляем погоду
        weather_text = weather_service.get_weather_text(weather)
        response += f"\n\n{weather_text}"

        # Удаляем статус
        await status_message.delete()

        # Отправляем ответ
        if update.message.chat.type == "private":
            await update.message.reply_text(f"🖼️ {response}")
        else:
            await update.message.reply_text(
                f"🖼️ {response}",
                reply_to_message_id=update.message.message_id
            )

        # Сохраняем контекст
        context_manager.save_context(user_id, f"[Фото] {user_message}", response)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото: {e}")
        await status_message.edit_text(
            "🖼️ Ой, какая красивая картинка! "
            "Жаль, что я немного ослепла от такого великолепия! 😄"
        )
