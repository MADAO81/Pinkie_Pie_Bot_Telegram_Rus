# bot/handlers/messages.py
"""
Message handler for text messages.

Author: MADAO81
Version: 2.5
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

logger = logging.getLogger(__name__)

mood_system = MoodSystem()
weather_service = WeatherService()
context_manager = ContextManager()


def normalize_city_name(city: str) -> str:
    """
    Приводит название города к именительному падежу (убирает окончания падежей).
    Поддерживает русские и английские названия.
    """
    city = city.strip()

    # Словарь известных падежей для популярных городов
    replacements = {
        'москве': 'Москва',
        'москвы': 'Москва',
        'москвой': 'Москва',
        'москву': 'Москва',
        'лондоне': 'Лондон',
        'лондона': 'Лондон',
        'лондоном': 'Лондон',
        'лондону': 'Лондон',
        'берлине': 'Берлин',
        'берлина': 'Берлин',
        'берлином': 'Берлин',
        'берлину': 'Берлин',
        'париже': 'Париж',
        'парижа': 'Париж',
        'парижем': 'Париж',
        'парижу': 'Париж',
        'санкт-петербурге': 'Санкт-Петербург',
        'санкт-петербурга': 'Санкт-Петербург',
        'петербурге': 'Санкт-Петербург',
    }

    city_lower = city.lower()
    if city_lower in replacements:
        return replacements[city_lower]

    # Универсальное правило для русских городов:
    # если заканчивается на 'е', 'ы', 'у', 'ю', 'я' — убираем последнюю букву
    # и пробуем добавить 'а' или 'я'
    if city.endswith(('е', 'ы', 'у', 'ю', 'я')):
        base = city[:-1]
        # Если основа заканчивается на согласную — добавляем 'а'
        if base and base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        return base + 'я'

    # Если город заканчивается на 'ой' или 'ем' (творительный падеж)
    if city.endswith('ой'):
        base = city[:-2]
        if base and base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        return base + 'я'
    if city.endswith('ем'):
        base = city[:-2]
        if base and base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        return base + 'я'

    return city.capitalize()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    # === CHECK IF WE SHOULD RESPOND ===
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
                logger.info(f"⏭️ Skipping message (not mentioned, 80% probability)")
                return
            else:
                logger.info(f"🎲 Responding to random message (20% probability)")

    status_message = await update.message.reply_text("💭 Thinking...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.text

        # === CHECK FOR WEATHER QUERY ===
        weather_keywords = [
            "погода", "weather", "за окном", "температура", "дождь",
            "солнце", "градус", "ветер", "холодно", "тепло", "метео"
        ]
        is_weather_query = any(keyword in user_message.lower() for keyword in weather_keywords)

        if is_weather_query:
            city = None
            city_raw = None

            # Паттерны для поиска города (русские и английские)
            patterns = [
                r'в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'для\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'температура\s+в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'in\s+([A-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'weather\s+in\s+([A-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'weather\s+([A-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
            ]

            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    city_raw = match.group(1).strip()
                    city_raw = re.sub(r'[.,!?;:]+$', '', city_raw)
                    # Нормализуем падеж
                    city = normalize_city_name(city_raw)
                    break

            # Если город найден и это не Ворсино/Боровск
            if city and city.lower() not in ["ворсино", "боровск", "ворсино.", "vorsino", "borovsk"]:
                logger.info(f"🌍 Weather requested for: {city}")
                weather = await weather_service.get_weather_by_city(city)
                if weather:
                    # Используем оригинальное название, которое прислал пользователь
                    display_city = city_raw if city_raw else city
                    weather_text = weather_service.get_weather_text(weather)
                    response = f"🌤️ *Погода в {display_city}*\n\n{weather_text}"
                else:
                    response = f"😅 Не могу найти город '{city_raw or city}'! Попробуй написать название на русском или английском. 🌧️"
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

        # === NORMAL RESPONSE ===
        mood, weather = await mood_system.determine_mood()
        mood_desc = "sad" if mood == "sad" else "happy"

        context_history = context_manager.get_context(user_id)

        response = await get_pinkie_response(
            user_message=user_message,
            mood_description=mood_desc,
            context_history=context_history
        )

        if not response:
            response = "😅 Oh-oh! My brain is overheating!\nLet's try again? 🎈"

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
        logger.error(f"❌ Error handling message: {e}")
        await status_message.edit_text(
            "😅 Oops! Something went wrong!\n"
            "Try again or send /help 💕"
        )
