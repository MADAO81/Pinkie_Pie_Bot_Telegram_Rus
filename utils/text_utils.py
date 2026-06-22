# bot/utils/text_utils.py
"""
Утилиты для работы с текстом.
Форматирование, эмодзи, фильтрация.

Автор: MADAO81
Версия: 2.0
"""

import re
import random
from typing import List, Optional
from bot.core.constants import EMOJIS


def get_random_emoji(mood: str = "happy") -> str:
    """
    Возвращает случайный эмодзи для настроения.

    Args:
        mood (str): Настроение ("happy", "sad", "neutral")

    Returns:
        str: Случайный эмодзи
    """
    emoji_list = EMOJIS.get(mood, EMOJIS["neutral"])
    return random.choice(emoji_list)


def add_emojis_to_text(text: str, mood: str = "happy", count: int = 2) -> str:
    """
    Добавляет эмодзи в текст.

    Args:
        text (str): Исходный текст
        mood (str): Настроение
        count (int): Количество эмодзи

    Returns:
        str: Текст с эмодзи
    """
    emojis = [get_random_emoji(mood) for _ in range(count)]
    return f"{' '.join(emojis)} {text}"


def clean_text(text: str) -> str:
    """
    Очищает текст от лишних символов.

    Args:
        text (str): Исходный текст

    Returns:
        str: Очищенный текст
    """
    # Удаляем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем пробелы в начале и конце
    text = text.strip()
    return text


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины.

    Args:
        text (str): Исходный текст
        max_length (int): Максимальная длина
        suffix (str): Суффикс для обрезанного текста

    Returns:
        str: Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_user_message(message: str, username: Optional[str] = None) -> str:
    """
    Форматирует сообщение пользователя.

    Args:
        message (str): Сообщение пользователя
        username (Optional[str]): Имя пользователя

    Returns:
        str: Отформатированное сообщение
    """
    if username:
        return f"{username}: {message}"
    return message


def format_bot_response(response: str, with_emojis: bool = True) -> str:
    """
    Форматирует ответ бота.

    Args:
        response (str): Ответ бота
        with_emojis (bool): Добавлять ли эмодзи

    Returns:
        str: Отформатированный ответ
    """
    if not with_emojis:
        return response

    # Добавляем эмодзи в конце, если их нет
    if not any(char in response for char in ["🎈", "🎉", "⭐", "💖", "😊", "🌸"]):
        response += f" {get_random_emoji('happy')}"

    return response


def extract_hashtags(text: str) -> List[str]:
    """
    Извлекает хэштеги из текста.

    Args:
        text (str): Исходный текст

    Returns:
        List[str]: Список хэштегов
    """
    hashtags = re.findall(r'#\w+', text)
    return hashtags


def remove_mentions(text: str) -> str:
    """
    Удаляет упоминания (@username) из текста.

    Args:
        text (str): Исходный текст

    Returns:
        str: Текст без упоминаний
    """
    return re.sub(r'@\w+', '', text)


def is_question(text: str) -> bool:
    """
    Проверяет, является ли текст вопросом.

    Args:
        text (str): Текст

    Returns:
        bool: True если текст содержит вопрос
    """
    question_words = ["кто", "что", "где", "когда", "почему", "зачем", "как", "сколько"]
    return (
        text.endswith("?") or
        any(word in text.lower() for word in question_words)
    )


def get_greeting() -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    Returns:
        str: Приветствие
    """
    from datetime import datetime
    hour = datetime.now().hour

    if 6 <= hour < 12:
        return "Доброе утро!"
    elif 12 <= hour < 18:
        return "Добрый день!"
    elif 18 <= hour < 23:
        return "Добрый вечер!"
    else:
        return "Доброй ночи!"
