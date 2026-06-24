# bot/handlers/messages.py
"""
Обработчик текстовых сообщений бота Пинки Пай.
Реагирует только на упоминания или с вероятностью 20%.
Поддерживает запросы погоды в любом городе (с падежами).

Автор: MADAO81
Версия: 2.3
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
    Приводит название города к именительному падежу.
    Поддерживает любые русские города через универсальные правила.
    """
    city = city.strip()
    city_lower = city.lower()
    
    # ===== 1. ТОЧНЫЕ ЗАМЕНЫ ДЛЯ ИЗВЕСТНЫХ ГОРОДОВ =====
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
        'риме': 'Рим',
        'рима': 'Рим',
        'римом': 'Рим',
        'риму': 'Рим',
        'токио': 'Токио',
        'осаке': 'Осака',
        'киеве': 'Киев',
        'минске': 'Минск',
        'варшаве': 'Варшава',
        'варшавы': 'Варшава',
        'варшавой': 'Варшава',
        'праге': 'Прага',
        'праги': 'Прага',
        'прагой': 'Прага',
        'вене': 'Вена',
        'афинах': 'Афины',
        'дубай': 'Дубай',
        'сидней': 'Сидней',
        'нью-йорке': 'Нью-Йорк',
        'нью-йорка': 'Нью-Йорк',
        'нью-йорком': 'Нью-Йорк',
        'лос-анджелесе': 'Лос-Анджелес',
        'шанхае': 'Шанхай',
        'пекине': 'Пекин',
        'сеуле': 'Сеул',
    }
    
    if city_lower in replacements:
        return replacements[city_lower]
    
    # ===== 2. УНИВЕРСАЛЬНОЕ ПРАВИЛО =====
    # Для города в предложном падеже: 'е' -> 'а' или 'я'
    if city_lower.endswith('е') and len(city) > 2:
        if city_lower.endswith('ие'):
            return city[:-2] + 'ия'
        else:
            base = city[:-1]
            if base[-1] in 'бвгджзйклмнпрстфхцчшщ':
                return base + 'а'
            else:
                return base + 'я'
    
    # Родительный падеж: 'ы' -> 'а' или 'я'
    elif city_lower.endswith('ы') and len(city) > 2:
        base = city[:-1]
        if base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        else:
            return base + 'я'
    
    # Дательный падеж: 'у' -> 'а' или 'я'
    elif city_lower.endswith('у') and len(city) > 2:
        base = city[:-1]
        if base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        else:
            return base + 'я'
    
    # Творительный падеж: 'ой' или 'ем'
    elif city_lower.endswith('ой') and len(city) > 3:
        base = city[:-2]
        if base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        else:
            return base + 'я'
    
    elif city_lower.endswith('ем') and len(city) > 3:
        base = city[:-2]
        if base[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return base + 'а'
        else:
            return base + 'я'
    
    # Дательный для мягких: 'ю' -> 'я'
    elif city_lower.endswith('ю') and len(city) > 2:
        return city[:-1] + 'я'
    
    # Родительный для мягких: 'я' -> 'я'
    elif city_lower.endswith('я') and len(city) > 2:
        return city
    
    return city.capitalize()


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
            # Пытаемся найти город в сообщении
            city = None
            
            patterns = [
                r'в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+в\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'погода\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
                r'для\s+([А-Яа-яA-Za-z\s\-]+?)(?:\s|,|\.|$|\))',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    city = match.group(1).strip()
                    city = re.sub(r'[.,!?;:]+$', '', city)
                    # Приводим к именительному падежу
                    city = normalize_city_name(city)
                    break
            
            # Если город найден и это не Ворсино/Боровск — показываем погоду в городе
            if city and city.lower() not in ["ворсино", "боровск", "ворсино."]:
                logger.info(f"🌍 Запрошен город (нормализован): {city}")
                weather = await weather_service.get_weather_by_city(city)
                if weather:
                    # Используем оригинальное название из API
                    city_name = weather.get('city_name', city)
                    weather_text = weather_service.get_weather_text(weather)
                    response = f"🌤️ *Погода в {city_name}*\n\n{weather_text}"
                else:
                    response = f"😅 Не могу найти город '{city}'! Попробуй написать название на русском или английском. 🌧️"
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
