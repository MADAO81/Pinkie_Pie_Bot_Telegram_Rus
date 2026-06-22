# bot/services/ai_service.py
"""
Сервис для работы с ИИ-моделями OpenAI:
- GPT-4-turbo (текстовые ответы)
- Vision API (анализ изображений)
- Whisper (распознавание голоса)

Автор: MADAO81
Версия: 2.0
"""

import logging
import base64
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from bot.config import Config
from bot.core.constants import SYSTEM_PROMPT

# Настройка логирования
logger = logging.getLogger(__name__)


async def get_pinkie_response(
    user_message: str,
    mood_description: str = "весёлое",
    context_history: Optional[List[Dict]] = None
) -> Optional[str]:
    """
    Основная функция для получения ответа от Пинки Пай через OpenAI.

    Args:
        user_message (str): Сообщение пользователя
        mood_description (str): Описание настроения ("весёлое" или "грустное")
        context_history (Optional[List[Dict]]): История диалога

    Returns:
        Optional[str]: Ответ от ИИ или None в случае ошибки
    """
    try:
        # Инициализируем клиент OpenAI
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        # Формируем системный промпт с учётом настроения
        system_prompt = SYSTEM_PROMPT
        if mood_description == "грустное":
            system_prompt += """

            ⚠️ ВАЖНО: СЕЙЧАС ТЫ В ГРУСТНОМ НАСТРОЕНИИ (Пинкамена Диана Пай)!
            - Говори тише, мягче и медленнее
            - Используй меньше восклицательных знаков (максимум 1-2 за сообщение)
            - Добавляй немного меланхолии в свои шутки
            - Но помни: ты НЕ должна вгонять других в депрессию
            - В конце сообщения добавляй что-то обнадёживающее, например: "Но всё будет хорошо... 🌧️💕"
            - Избегай излишней энергии и прыжков через голову
            """

        # Собираем сообщения
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Сейчас у тебя настроение: {mood_description}"}
        ]

        # Добавляем контекст истории (последние 10 сообщений)
        if context_history:
            messages.extend(context_history[-10:])

        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": user_message})

        # Отправляем запрос к OpenAI
        logger.info(f"🧠 Запрос к OpenAI (модель: {Config.OPENAI_MODEL})...")

        response = await client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            max_tokens=Config.OPENAI_MAX_TOKENS,
            temperature=Config.OPENAI_TEMPERATURE,
            timeout=30.0
        )

        # Получаем ответ
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ OpenAI вернул пустой ответ")
            return None

    except ImportError:
        logger.error("❌ Библиотека openai не установлена. Установите: pip install openai")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при запросе к OpenAI: {e}")
        return None


async def analyze_image(
    image_data: bytes,
    user_message: Optional[str] = None,
    mood_description: str = "весёлое"
) -> Optional[str]:
    """
    Анализ изображения через OpenAI Vision API.

    Args:
        image_data (bytes): Данные изображения
        user_message (Optional[str]): Сообщение пользователя к картинке
        mood_description (str): Описание настроения

    Returns:
        Optional[str]: Комментарий к изображению или None в случае ошибки
    """
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        # Формируем системный промпт
        system_prompt = SYSTEM_PROMPT
        if mood_description == "грустное":
            system_prompt += "\n\nСейчас ты в грустном настроении, но всё равно стараешься быть доброй."

        # Кодируем изображение в base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Формируем запрос
        content = [
            {
                "type": "text",
                "text": f"Пользователь отправил изображение. {user_message if user_message else 'Опиши, что ты видишь на картинке, и прокомментируй это в своём стиле.'}"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]

        logger.info("🖼️ Запрос к OpenAI Vision API...")

        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ Vision API вернул пустой ответ")
            return None

    except ImportError:
        logger.error("❌ Библиотека openai не установлена")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе изображения: {e}")
        return None


async def transcribe_audio(
    audio_data: bytes,
    file_extension: str = ".ogg"
) -> Optional[str]:
    """
    Транскрибация голосового сообщения через OpenAI Whisper.

    Args:
        audio_data (bytes): Данные аудио
        file_extension (str): Расширение файла

    Returns:
        Optional[str]: Распознанный текст или None в случае ошибки
    """
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        # Создаём временную директорию для аудио
        audio_dir = Path(Config.AUDIO_DIR)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Сохраняем аудио во временный файл
        audio_path = audio_dir / f"voice_{int(time.time())}{file_extension}"
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        logger.info(f"🎤 Отправка аудио в Whisper (файл: {audio_path.name})...")

        # Отправляем в Whisper
        with open(audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        # Удаляем временный файл
        try:
            os.remove(audio_path)
        except:
            pass

        if transcription and transcription.text:
            logger.info(f"✅ Транскрибация успешна: {transcription.text[:50]}...")
            return transcription.text.strip()
        else:
            logger.warning("⚠️ Whisper вернул пустой ответ")
            return None

    except ImportError:
        logger.error("❌ Библиотека openai не установлена")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при транскрибации: {e}")
        return None


async def check_ai_health() -> Dict[str, Any]:
    """
    Проверяет доступность OpenAI сервисов.

    Returns:
        Dict[str, Any]: Статусы сервисов
    """
    status = {
        'openai': False,
        'vision': False,
        'whisper': False,
        'any_available': False
    }

    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        # Проверяем основную модель
        try:
            test_response = await client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=10.0
            )
            if test_response.choices:
                status['openai'] = True
                logger.info("✅ OpenAI GPT доступен")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI GPT недоступен: {e}")

        # Vision доступен если доступен GPT-4
        status['vision'] = status['openai']
        # Whisper доступен если доступен OpenAI
        status['whisper'] = status['openai']

        status['any_available'] = status['openai']

    except ImportError:
        logger.error("❌ Библиотека openai не установлена")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке OpenAI: {e}")

    return status


def get_ai_status_message(status: Dict[str, Any]) -> str:
    """
    Возвращает форматированное сообщение о статусе ИИ.

    Args:
        status (Dict[str, Any]): Статусы сервисов

    Returns:
        str: Форматированное сообщение
    """
    if not status['any_available']:
        return "🧠 ИИ: ❌ *Недоступен* (проверьте OPENAI_API_KEY в .env)"

    openai_status = "✅ Доступен" if status['openai'] else "❌ Недоступен"
    vision_status = "✅ Доступен" if status['vision'] else "❌ Недоступен"
    whisper_status = "✅ Доступен" if status['whisper'] else "❌ Недоступен"

    return (
        f"🧠 *Статус ИИ:*\n\n"
        f"🤖 OpenAI GPT: {openai_status}\n"
        f"🖼️ Vision API: {vision_status}\n"
        f"🎤 Whisper: {whisper_status}"
    )


def format_context_for_openai(context_history: List[Dict]) -> List[Dict]:
    """
    Форматирует историю диалога для OpenAI.

    Args:
        context_history (List[Dict]): История диалога

    Returns:
        List[Dict]: Отформатированная история
    """
    formatted = []
    for msg in context_history:
        if msg.get('role') == 'user':
            formatted.append({
                "role": "user",
                "content": msg.get('content', '')
            })
        elif msg.get('role') == 'assistant':
            formatted.append({
                "role": "assistant",
                "content": msg.get('content', '')
            })
    return formatted
