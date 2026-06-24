# bot/handlers/messages.py
"""
Обработчик текстовых сообщений бота Пинки Пай.
Реагирует только на упоминания или с вероятностью 20%.

Автор: MADAO81
Версия: 2.0
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.ai_service import get_pinkie_response
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка текстовых сообщений.
    Реагирует только если:
    - сообщение адресовано боту (@username или ответ на сообщение бота)
    - или с вероятностью 20% (каждое 5-е сообщение)
    """
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # === ПРОВЕРКА: нужно ли реагировать ===
    
    # 1. В личных сообщениях — всегда отвечаем
    if update.message.chat.type == "private":
        pass  # пропускаем проверки
    
    # 2. В группах — проверяем
    else:
        # Получаем имя бота
        bot_username = context.bot.username
        
        # Проверяем, упомянут ли бот
        is_mentioned = False
        
        # Проверяем текст на упоминание @username
        if update.message.text and f"@{bot_username}" in update.message.text.lower():
            is_mentioned = True
        
        # Проверяем, является ли сообщение ответом на сообщение бота
        if update.message.reply_to_message:
            if update.message.reply_to_message.from_user.username == bot_username:
                is_mentioned = True
        
        # Если бот не упомянут — проверяем случайную вероятность (20%)
        if not is_mentioned:
            # 20% вероятность ответить на случайное сообщение
            if random.random() >= 0.2:
                logger.info(f"⏭️ Пропускаем сообщение (не упомянут, 80% вероятности)")
                return
            else:
                logger.info(f"🎲 Ответим на случайное сообщение (20% вероятности)")

    # === ГЕНЕРАЦИЯ ОТВЕТА ===
    status_message = await update.message.reply_text("💭 Думаю...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.text

        # Определяем настроение
        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        # Получаем контекст диалога
        context_history = context_manager.get_context(user_id)

        # Генерируем ответ
        response = await get_pinkie_response(
            user_message=user_message,
            mood_description=mood_desc,
            context_history=context_history
        )

        if not response:
            response = "😅 Ой-ой-ой! Что-то у меня мозги закипели!\nДавай попробуем ещё раз? 🎈"

        # Добавляем погоду только если пользователь спрашивает
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер", "холодно", "тепло", "метео"]
        if any(keyword in user_message.lower() for keyword in weather_keywords):
            weather_text = weather_service.get_weather_text(weather)
            response += f"\n\n{weather_text}"

        await status_message.delete()

        if update.message.chat.type == "private":
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                response,
                reply_to_message_id=update.message.message_id
            )

        context_manager.save_context(user_id, user_message, response)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так!\n"
            "Попробуй ещё раз или напиши /help для справки! 💕"
        )
