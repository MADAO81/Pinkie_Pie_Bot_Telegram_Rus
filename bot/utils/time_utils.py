# bot/utils/time_utils.py
"""
Утилиты для работы со временем.
Проверка рабочего времени бота.

Автор: MADAO81
Версия: 2.0
"""

from datetime import datetime
from bot.config import Config


def is_working_hours() -> bool:
    """
    Проверяет, работает ли бот в данный момент.

    Returns:
        bool: True если сейчас рабочее время
    """
    now = datetime.now()
    current_hour = now.hour

    return Config.WORK_START_HOUR <= current_hour < Config.WORK_END_HOUR


def get_working_status_message() -> str:
    """
    Возвращает сообщение о статусе работы бота.

    Returns:
        str: Сообщение о статусе работы
    """
    if is_working_hours():
        return None

    return (
        "🌸 Привет! Я сейчас отдыхаю, так как моё рабочее время "
        f"с {Config.WORK_START_HOUR}:00 до {Config.WORK_END_HOUR}:00.\n\n"
        "Приходи завтра — я буду рада поболтать! "
        "А пока можешь посмотреть рецепты на andychef.ru 🧁\n\n"
        "Спокойной ночи! 🌙"
    )


def get_current_time() -> str:
    """
    Возвращает текущее время в формате ЧЧ:ММ.

    Returns:
        str: Текущее время
    """
    now = datetime.now()
    return now.strftime("%H:%M")


def get_current_date() -> str:
    """
    Возвращает текущую дату в формате ДД.ММ.ГГГГ.

    Returns:
        str: Текущая дата
    """
    now = datetime.now()
    return now.strftime("%d.%m.%Y")


def get_weekday() -> str:
    """
    Возвращает название текущего дня недели на русском.

    Returns:
        str: Название дня недели
    """
    weekdays = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье"
    }
    now = datetime.now()
    return weekdays.get(now.weekday(), "Неизвестно")


def get_remaining_work_time() -> str:
    """
    Возвращает оставшееся рабочее время.

    Returns:
        str: Оставшееся время работы
    """
    if not is_working_hours():
        return "Бот не работает"

    now = datetime.now()
    end_time = now.replace(hour=Config.WORK_END_HOUR, minute=0, second=0, microsecond=0)
    remaining = end_time - now

    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    if hours > 0:
        return f"{hours} ч {minutes} мин"
    else:
        return f"{minutes} мин"
