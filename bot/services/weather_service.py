# bot/services/weather_service.py
"""
Сервис для работы с Яндекс Погодой.
Получение текущей погоды в Боровском районе Калужской области.

Автор: MADAO81
Версия: 2.0
"""

import logging
from typing import Optional, Dict
import aiohttp
from bot.config import Config

# Настройка логирования
logger = logging.getLogger(__name__)


class WeatherService:
    """
    Класс для получения погоды через API Яндекс Погоды.
    """

    def __init__(self):
        """Инициализация сервиса погоды."""
        self.api_key = Config.YANDEX_WEATHER_API_KEY
        self.lat = Config.YANDEX_WEATHER_LAT
        self.lon = Config.YANDEX_WEATHER_LON
        self.base_url = "https://api.weather.yandex.ru/v2/forecast"

    async def get_weather(self) -> Optional[Dict]:
        """
        Получение текущей погоды через Яндекс Погоду.

        Returns:
            Optional[Dict]: Данные о погоде или None в случае ошибки
        """
        if not self.api_key:
            logger.error("❌ YANDEX_WEATHER_API_KEY не найден в .env файле!")
            return None

        try:
            headers = {
                "X-Yandex-API-Key": self.api_key
            }

            params = {
                "lat": self.lat,
                "lon": self.lon,
                "lang": "ru_RU",
                "limit": 1
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=10.0
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return self._parse_weather(data)
                    elif response.status == 403:
                        logger.error("❌ Ошибка: неверный API ключ Яндекс Погоды")
                        return None
                    else:
                        logger.error(f"❌ Ошибка Яндекс Погоды: {response.status}")
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения с Яндекс Погодой: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении погоды: {e}")
            return None

    def _parse_weather(self, data: Dict) -> Dict:
        """
        Парсинг данных о погоде.

        Args:
            data (Dict): Данные от API

        Returns:
            Dict: Обработанные данные о погоде
        """
        try:
            fact = data.get("fact", {})
            forecast = data.get("forecasts", [{}])[0]

            weather = {
                "temperature": fact.get("temp", 0),
                "feels_like": fact.get("feels_like", 0),
                "humidity": fact.get("humidity", 0),
                "pressure": fact.get("pressure_mm", 750),
                "wind_speed": fact.get("wind_speed", 0),
                "condition": fact.get("condition", "clear"),
                "description": self._translate_condition(
                    fact.get("condition", "clear")
                ),
                "is_bad": False
            }

            # Определяем, плохая ли погода
            bad_conditions = [
                "rain", "heavy-rain", "snow", "heavy-snow",
                "sleet", "thunderstorm", "drizzle", "overcast",
                "rain-and-snow"
            ]
            if weather["condition"] in bad_conditions:
                weather["is_bad"] = True

            return weather

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга погоды: {e}")
            return {
                "temperature": 0,
                "feels_like": 0,
                "humidity": 0,
                "pressure": 750,
                "wind_speed": 0,
                "condition": "clear",
                "description": "неизвестно",
                "is_bad": False
            }

    def _translate_condition(self, condition: str) -> str:
        """
        Перевод условий погоды на русский.

        Args:
            condition (str): Условие погоды на английском

        Returns:
            str: Условие погоды на русском
        """
        conditions = {
            "clear": "ясно",
            "partly-cloudy": "переменная облачность",
            "cloudy": "облачно",
            "overcast": "пасмурно",
            "rain": "дождь",
            "heavy-rain": "сильный дождь",
            "snow": "снег",
            "heavy-snow": "сильный снег",
            "sleet": "мокрый снег",
            "thunderstorm": "гроза",
            "drizzle": "морось",
            "rain-and-snow": "дождь со снегом"
        }
        return conditions.get(condition, condition)

    def is_bad_weather(self, weather_data: Optional[Dict]) -> bool:
        """
        Проверка, является ли погода плохой.

        Args:
            weather_data (Optional[Dict]): Данные о погоде

        Returns:
            bool: True если погода плохая
        """
        if not weather_data:
            return False
        return weather_data.get("is_bad", False)

    def get_weather_text(self, weather_data: Optional[Dict]) -> str:
        """
        Возвращает текстовое описание погоды.

        Args:
            weather_data (Optional[Dict]): Данные о погоде

        Returns:
            str: Текстовое описание погоды
        """
        if not weather_data:
            return "🌤️ Погода: неизвестно"

        temp = weather_data.get("temperature", 0)
        description = weather_data.get("description", "неизвестно")
        feels_like = weather_data.get("feels_like", 0)

        emoji = "☀️" if not weather_data.get("is_bad", False) else "🌧️"

        return (
            f"{emoji} В Боровске сейчас {description}, "
            f"{temp}°C (ощущается как {feels_like}°C)"
        )
