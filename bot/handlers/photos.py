# bot/handlers/photos.py
"""
Photo handler for Pinkie Pie bot.

Author: MADAO81
Version: 2.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.ai_service import analyze_image
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photos."""
    logger.info("📸 ФУНКЦИЯ handle_photo ВЫЗВАНА!")

    if not is_working_hours():
        logger.info("⏰ Не рабочее время, фото игнорируется")
        return

    if not mood_system.should_comment():
        logger.info("🎲 Решено НЕ комментировать фото")
        return

    status_message = await update.message.reply_text("🖼️ Смотрю на картинку... Сейчас что-то придумаю!")

    try:
        user_id = update.effective_user.id
        user_message = update.message.caption or "Красивая картинка!"

        # Получаем фото в максимальном качестве
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()
        
        logger.info(f"📸 Фото получено, размер: {len(image_data)} байт")

        # Определяем настроение
        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        # Анализируем изображение через Vision API
        logger.info("🖼️ Отправка запроса в Vision API...")
        response = await analyze_image(
            image_data=bytes(image_data),
            user_message=user_message,
            mood_description=mood_desc
        )
        logger.info(f"🖼️ Ответ Vision API: {response[:100] if response else 'None'}")

        if not response:
            response = "🖼️ Ой, какая красивая картинка! Жаль, что у меня сейчас глаза разбегаются от такого великолепия! 😄"

        # Проверяем, спрашивает ли пользователь о погоде в подписи к фото
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер"]
        if user_message and any(keyword in user_message.lower() for keyword in weather_keywords):
            weather_text = weather_service.get_weather_text(weather)
            response += f"\n\n{weather_text}"

        await status_message.delete()

        logger.info(f"📤 Отправлен ответ пользователю: {response[:100] if response else 'None'}")

        if update.message.chat.type == "private":
            await update.message.reply_text(f"🖼️ {response}")
        else:
            await update.message.reply_text(
                f"🖼️ {response}",
                reply_to_message_id=update.message.message_id
            )

        context_manager.save_context(user_id, f"[Фото] {user_message}", response)
        logger.info("✅ Фото обработано успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото: {e}")
        await status_message.edit_text(
            "🖼️ Ой, какая красивая картинка! "
            "Жаль, что я немного ослепла от такого великолепия! 😄"
        )
