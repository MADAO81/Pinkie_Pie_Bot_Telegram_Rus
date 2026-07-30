# bot/handlers/photos.py
"""
Photo handler for Pinkie Pie bot.
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

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фотографий — только по запросу и только на свои упоминания."""
    logger.info("📸 Фото получено")

    if not is_working_hours():
        logger.info("⏰ Не рабочее время, фото игнорируется")
        return

    # === Проверка: упомянута ли Пинки ===
    if update.message.chat.type != "private":
        bot_username = context.bot.username
        is_mentioned = False

        # Проверяем упоминание в тексте
        if update.message.caption and f"@{bot_username}" in update.message.caption.lower():
            is_mentioned = True

        # Проверяем ответ на сообщение бота
        if update.message.reply_to_message:
            if update.message.reply_to_message.from_user.username == bot_username:
                is_mentioned = True

        if not is_mentioned:
            logger.info(f"⏭️ Пропускаем фото в группе (не моё @)")
            return

    # === Проверка: просит ли пользователь прокомментировать фото ===
    user_message = update.message.caption or ""
    ask_keywords = ["что", "это", "прокомменти", "расскажи", "опиши", "скажи", "посмотри", "что на картинке"]
    is_asking = any(keyword in user_message.lower() for keyword in ask_keywords)

    if not is_asking and update.message.chat.type != "private":
        await update.message.reply_text(
            "🖼️ Красивая картинка! Если хочешь, чтобы я её описала — спроси, например: «что на картинке?» 🎈"
        )
        return

    # === Если просят — комментируем ===
    status_message = await update.message.reply_text("🖼️ Смотрю на картинку... Сейчас что-то придумаю!")

    try:
        user_id = update.effective_user.id
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()

        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        response = await analyze_image(
            image_data=bytes(image_data),
            user_message=user_message,
            mood_description=mood_desc
        )

        if not response:
            response = "🖼️ Ой, какая красивая картинка! 😄"

        # Проверяем, спрашивает ли пользователь о погоде в подписи к фото
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер"]
        if any(keyword in user_message.lower() for keyword in weather_keywords):
            weather_text = weather_service.get_weather_text(weather)
            response += f"\n\n{weather_text}"

        await status_message.delete()

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
            "Что-то пошло не так, но она всё равно прекрасна! 😄"
        )
