# bot/handlers/messages.py
"""
Обработчик текстовых сообщений бота Пинки Пай.
Реагирует только на упоминания или с вероятностью 20%.
Поддерживает запросы погоды в любом городе (с падежами).
Использует pymorphy2 для автоматической нормализации русских городов.

Автор: MADAO81
Версия: 2.9
"""

import logging
import random
import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.mood_system import MoodSystem
from bot.services.ai_service import get_pinkie_response
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.context_manager import ContextManager
import pymorphy2

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()
morph = pymorphy2.MorphAnalyzer()


def normalize_city_name(city: str) -> str:
    """
    Приводит название города к именительному падежу с помощью pymorphy2.
    Если не удаётся — возвращает исходное название с заглавной буквы.
    """
    city = city.strip()
    if not city:
        return city

    try:
        parsed = morph.parse(city)[0]
        normalized = parsed.inflect({'nomn'})
        if normalized:
            return normalized.word.capitalize()
    except Exception:
        pass

    return city.capitalize()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка текстовых сообщений.
    """
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # === ПРОВЕРКА: нужно ли реагировать ===
    if update.message.chat.type == "private":
        pass
    else:
        bot_username = context.bot.username
        is_mentioned = False
        
        if update.message.text and f"@{bot_username}" in update.message.text.lower():
            is_mentioned = True
        
        if update.message.reply_to_message:
            if update.message.reply_to_message.from_user.username == bot_username:
                is_mentioned = True
        
        if not is_mentioned:
            if random.random() >= 0.2:
                logger.info(f"⏭️ Пропускаем сообщение")
                return
            else:
                logger.info(f"🎲 Ответим на случайное сообщение")

    status_message = await update.message.reply_text("💭 Думаю...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.text

        # === ПРОВЕРКА НА ЗАПРОС ПОГОДЫ ===
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер", "холодно", "тепло", "метео"]
        is_weather_query = any(keyword in user_message.lower() for keyword in weather_keywords)

        if is_weather_query:
            city_original = None  # для отображения пользователю
            city_normalized = None  # для поиска в API
            
            patterns = [
                r'во\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+во\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'для\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'температура\s+во\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'температура\s+в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'in\s+([A-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'weather\s+in\s+([A-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'weather\s+([A-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    city_original = match.group(1).strip()
                    city_original = re.sub(r'[.,!?;:]+$', '', city_original)
                    # Нормализуем для поиска в API
                    city_normalized = normalize_city_name(city_original)
                    break
            
            # Если город найден и это не Ворсино/Боровск
            if city_normalized and city_normalized.lower() not in ["ворсино", "боровск", "ворсино."]:
                logger.info(f"🌍 Запрошен город: {city_original} (нормализован: {city_normalized})")
                weather = await weather_service.get_weather_by_city(city_normalized)
                if weather:
                    # Передаём city_original для сохранения падежа в ответе
                    weather_text = weather_service.get_weather_text(weather, city_original)
                    response = f"🌤️ *Погода в {city_original}*\n\n{weather_text}"
                else:
                    response = f"😅 Не могу найти город '{city_original}'! Попробуй написать название на русском или английском. 🌧️"
            else:
                # По умолчанию — Ворсино
                weather = await weather_service.get_weather()
                if weather:
                    weather_text = weather_service.get_weather_text(weather)
                    response = f"🌤️ *Погода в Ворсино*\n\n{weather_text}"
                else:
                    response = "😅 Не могу узнать погоду! Попробуй позже! 🌧️"
            
            await status_message.delete()
            await update.message.reply_text(response, parse_mode="Markdown")
            return

        # === ОБЫЧНЫЙ ОТВЕТ ===
        mood, weather = await mood_system.determine_mood()
        mood_desc = "грустное" if mood == "sad" else "весёлое"

        context_history = context_manager.get_context(user_id)

        response = await get_pinkie_response(
            user_message=user_message,
            mood_description=mood_desc,
            context_history=context_history
        )

        if not response:
            response = "😅 Ой-ой-ой! Что-то у меня мозги закипели!\nДавай попробуем ещё раз? 🎈"

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
