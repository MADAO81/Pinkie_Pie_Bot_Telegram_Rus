# bot/services/ai_service.py
"""
AI сервис для бота Пинки Пай.
Гибридный режим: DeepSeek (текст) + OpenAI (картинки + голос).

Автор: MADAO81
Версия: 3.2
"""

import logging
import base64
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from bot.config import Config
from bot.core.constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def get_pinkie_response(
    user_message: str,
    mood_description: str = "happy",
    context_history: Optional[List[Dict]] = None
) -> Optional[str]:
    """Генерирует ответ от Пинки Пай через DeepSeek (через ProxyAPI)."""
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/openrouter/v1"
        )

        system_prompt = SYSTEM_PROMPT
        if mood_description == "sad":
            system_prompt += """

            ⚠️ IMPORTANT: YOU ARE IN A SAD MOOD RIGHT NOW!
            - Speak more softly, gently, and slowly
            - Use fewer exclamation marks (maximum 1-2 per message)
            - Add a touch of melancholy to your jokes
            - But remember: you must NOT make others depressed
            - End the message with something reassuring
            - Avoid excessive energy
            """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Your current mood is: {mood_description}"}
        ]

        if context_history:
            messages.extend(context_history[-10:])

        messages.append({"role": "user", "content": user_message})

        logger.info(f"🧠 Запрос к DeepSeek (модель: {Config.DEEPSEEK_MODEL})...")

        response = await client.chat.completions.create(
            model=Config.DEEPSEEK_MODEL,
            messages=messages,
            max_tokens=Config.DEEPSEEK_MAX_TOKENS,
            temperature=Config.DEEPSEEK_TEMPERATURE,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ DeepSeek вернул пустой ответ")
            return None

    except Exception as e:
        logger.error(f"❌ DeepSeek error: {e}")
        return None


async def analyze_image(
    image_data: bytes,
    user_message: Optional[str] = None,
    mood_description: str = "happy"
) -> Optional[str]:
    """Анализирует изображение через OpenAI Vision API (через ProxyAPI)."""
    logger.info("🖼️ Request to OpenAI Vision API...")
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/v1"
        )

        system_prompt = SYSTEM_PROMPT
        if mood_description == "sad":
            system_prompt += "\n\nYou are in a sad mood, but still trying to be kind."

        base64_image = base64.b64encode(image_data).decode('utf-8')

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"User sent an image. {user_message if user_message else 'Describe what you see in the image and comment on it in your style.'}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        logger.info("🖼️ Sending request to OpenAI Vision API...")

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ Vision API returned empty response")
            return None

    except Exception as e:
        logger.error(f"❌ Error analyzing image: {e}")
        return None


async def transcribe_audio(
    audio_data: bytes,
    file_extension: str = ".ogg"
) -> Optional[str]:
    """Транскрибирует аудио через OpenAI Whisper (через ProxyAPI)."""
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/v1"
        )

        audio_dir = Path(Config.AUDIO_DIR)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"voice_{int(time.time())}{file_extension}"
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        logger.info(f"🎤 Sending audio to Whisper...")

        with open(audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        try:
            os.remove(audio_path)
        except:
            pass

        if transcription and transcription.text:
            logger.info(f"✅ Transcription successful: {transcription.text[:50]}...")
            return transcription.text.strip()
        else:
            logger.warning("⚠️ Whisper returned empty response")
            return None

    except Exception as e:
        logger.error(f"❌ Whisper error: {e}")
        return None


async def check_ai_health() -> Dict[str, Any]:
    """Проверяет доступность сервисов."""
    status = {
        'deepseek': False,
        'vision': False,
        'whisper': False,
        'any_available': False
    }

    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/openrouter/v1"
        )

        response = await client.models.list()
        if response:
            status['deepseek'] = True
            logger.info("✅ DeepSeek доступен")
    except Exception as e:
        logger.warning(f"⚠️ DeepSeek недоступен: {e}")

    status['vision'] = True
    status['whisper'] = True
    status['any_available'] = status['deepseek']

    return status


def get_ai_status_message(status: Dict[str, Any]) -> str:
    """Возвращает форматированное сообщение о статусе ИИ."""
    if not status['any_available']:
        return "🧠 ИИ: ❌ *Недоступен* (проверьте ключи в .env)"

    deepseek_status = "✅ Доступен" if status['deepseek'] else "❌ Недоступен"
    vision_status = "✅ Доступен" if status['vision'] else "❌ Недоступен"
    whisper_status = "✅ Доступен" if status['whisper'] else "❌ Недоступен"

    return (
        f"🧠 *Статус ИИ:*\n\n"
        f"🔵 DeepSeek: {deepseek_status}\n"
        f"🖼️ Vision: {vision_status}\n"
        f"🎤 Whisper: {whisper_status}"
    )


def format_context_for_deepseek(context_history: List[Dict]) -> List[Dict]:
    """Форматирует историю диалога для DeepSeek."""
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
