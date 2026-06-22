# bot/core/mood_system.py
"""
Система настроений Пинки Пай.
Определяет настроение на основе погоды в Боровском районе.

Автор: MADAO81
Версия: 2.0
"""

import random
from typing import Tuple, Optional, Dict
from bot.services.weather_service import WeatherService
from bot.config import Config


class MoodSystem:
    """
    Класс для управления настроением Пинки Пай.
    Настроение зависит от погоды в Боровском районе.
    """

    def __init__(self):
        """Инициализация системы настроений."""
        self.weather_service = WeatherService()
        self.sad_probability = Config.SAD_PROBABILITY
        self.current_mood = "happy"
        self.current_weather = None

    async def determine_mood(self) -> Tuple[str, Optional[Dict]]:
        """
        Определяет настроение на основе текущей погоды.

        Returns:
            Tuple[str, Optional[Dict]]: (настроение, данные о погоде)
            Настроение может быть "happy" или "sad"
        """
        # Получаем погоду
        weather = await self.weather_service.get_weather()
        self.current_weather = weather

        # Если погода не получена, возвращаем весёлое настроение
        if not weather:
            self.current_mood = "happy"
            return "happy", None

        # Проверяем, плохая ли погода
        if self.weather_service.is_bad_weather(weather):
            # Плохая погода — проверяем вероятность грусти
            if random.random() < self.sad_probability:
                self.current_mood = "sad"
                return "sad", weather

        # По умолчанию — весёлое настроение
        self.current_mood = "happy"
        return "happy", weather

    def get_mood_text(self, mood: str) -> str:
        """
        Возвращает текстовое описание настроения.

        Args:
            mood (str): Настроение ("happy" или "sad")

        Returns:
            str: Текстовое описание настроения
        """
        if mood == "sad":
            return "😔 Пинкамина Диана Пай сегодня немного грустит... Но она всё равно рада вас видеть!"
        return "🎈 Пинки Пай в отличном настроении! Вечеринка продолжается!"

    def get_mood_emoji(self, mood: str) -> str:
        """
        Возвращает эмодзи для текущего настроения.

        Args:
            mood (str): Настроение ("happy" или "sad")

        Returns:
            str: Эмодзи настроения
        """
        if mood == "sad":
            return "🌧️"
        return "🎈"

    def should_comment(self) -> bool:
        """
        Определяет, нужно ли комментировать сообщение.
        Вероятность комментария — 20%.

        Returns:
            bool: True если нужно прокомментировать
        """
        return random.random() < 0.2

    def get_current_mood(self) -> str:
        """
        Возвращает текущее настроение.

        Returns:
            str: Текущее настроение
        """
        return self.current_mood

    def get_current_weather(self) -> Optional[Dict]:
        """
        Возвращает текущие данные о погоде.

        Returns:
            Optional[Dict]: Данные о погоде или None
        """
        return self.current_weather
