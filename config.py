# bot/config.py
"""
Конфигурация бота Пинки Пай.
Загрузка переменных окружения из .env файла.

Автор: MADAO81
Версия: 2.0
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Класс конфигурации бота."""
    
    # ========== TELEGRAM ==========
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # ========== OPENAI ==========
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", 1000))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.85))
    
    # ========== YANDEX WEATHER ==========
    YANDEX_WEATHER_API_KEY = os.getenv("YANDEX_WEATHER_API_KEY")
    YANDEX_WEATHER_LAT = float(os.getenv("YANDEX_WEATHER_LAT", 55.2067))
    YANDEX_WEATHER_LON = float(os.getenv("YANDEX_WEATHER_LON", 36.6550))
    
    # ========== РАБОЧЕЕ ВРЕМЯ ==========
    WORK_START_HOUR = int(os.getenv("WORK_START_HOUR", 9))
    WORK_END_HOUR = int(os.getenv("WORK_END_HOUR", 20))
    
    # ========== НАСТРОЕНИЕ ==========
    SAD_PROBABILITY = float(os.getenv("SAD_PROBABILITY", 0.2))
    
    # ========== КОНТЕКСТ ==========
    CONTEXT_EXPIRE_DAYS = int(os.getenv("CONTEXT_EXPIRE_DAYS", 30))
    
    # ========== РЕЦЕПТЫ ==========
    RECIPE_SEND_TIME = os.getenv("RECIPE_SEND_TIME", "12:00")
    RECIPE_URL = os.getenv("RECIPE_URL", "https://andychef.ru")
    
    # ========== ПУТИ ==========
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    AUDIO_DIR = DATA_DIR / "audio"
    
    # Создаём директории
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # ========== БАЗА ДАННЫХ ==========
    CONVERSATIONS_DB = DATA_DIR / "conversations.db"
    
    # ========== СТАРЫЕ ПАРАМЕТРЫ (для обратной совместимости) ==========
    # Удаляем старые параметры, оставляем заглушки
    GIGACHAT_CREDENTIALS = None
    GIGACHAT_SCOPE = None
    YANDEXGPT_API_KEY = None
    YANDEXGPT_FOLDER_ID = None