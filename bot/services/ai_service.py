# bot/services/ai_service.py
"""
AI service for OpenAI integration (GPT-4-turbo, Vision, Whisper).

Author: MADAO81
Version: 2.0
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

logger = logging.getLogger(__name__)


async def get_pinkie_response(
    user_message: str,
    mood_description: str = "happy",
    context_history: Optional[List[Dict]] = None
) -> Optional[str]:
    """Generates a response from Pinkie Pie using OpenAI."""
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        system_prompt = SYSTEM_PROMPT
        if mood_description == "sad":
            system_prompt += """

            ⚠️ IMPORTANT: YOU ARE IN A SAD MOOD RIGHT NOW (Pinkamena Diane Pie)!
            - Speak more softly, gently, and slowly
            - Use fewer exclamation marks (maximum 1-2 per message)
            - Add a touch of melancholy to your jokes
            - But remember: you must NOT make others depressed
            - End the message with something reassuring
            - Avoid excessive energy and bouncing
            """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Your current mood is: {mood_description}"}
        ]

        if context_history:
            messages.extend(context_history[-10:])

        messages.append({"role": "user", "content": user_message})

        logger.info(f"🧠 Request to OpenAI (model: {Config.OPENAI_MODEL})...")

        response = await client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            max_tokens=Config.OPENAI_MAX_TOKENS,
            temperature=Config.OPENAI_TEMPERATURE,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ OpenAI returned empty response")
            return None

    except ImportError:
        logger.error("❌ openai library not installed. Run: pip install openai")
        return None
    except Exception as e:
        logger.error(f"❌ Error calling OpenAI: {e}")
        return None


async def analyze_image(
    image_data: bytes,
    user_message: Optional[str] = None,
    mood_description: str = "happy"
) -> Optional[str]:
    """Analyzes an image using OpenAI Vision API."""
    logger.info("🖼️ Запрос к OpenAI Vision API...")
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

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

        logger.info("🖼️ Отправка запроса в OpenAI Vision API...")

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
            logger.warning("⚠️ Vision API вернул пустой ответ")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при анализе изображения: {e}")
        return None


async def transcribe_audio(
    audio_data: bytes,
    file_extension: str = ".ogg"
) -> Optional[str]:
    """Transcribes audio using OpenAI Whisper."""
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

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
                language="en"
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

    except ImportError:
        logger.error("❌ openai library not installed")
        return None
    except Exception as e:
        logger.error(f"❌ Error transcribing audio: {e}")
        return None


async def check_ai_health() -> Dict[str, Any]:
    """Checks OpenAI service availability."""
    status = {
        'openai': False,
        'vision': False,
        'whisper': False,
        'any_available': False
    }

    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        try:
            test_response = await client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=10.0
            )
            if test_response.choices:
                status['openai'] = True
                logger.info("✅ OpenAI GPT available")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI GPT unavailable: {e}")

        status['vision'] = status['openai']
        status['whisper'] = status['openai']
        status['any_available'] = status['openai']

    except ImportError:
        logger.error("❌ openai library not installed")
    except Exception as e:
        logger.error(f"❌ Error checking OpenAI: {e}")

    return status


def get_ai_status_message(status: Dict[str, Any]) -> str:
    """Returns formatted AI status message."""
    if not status['any_available']:
        return "🧠 AI: ❌ *Unavailable* (check OPENAI_API_KEY in .env)"

    openai_status = "✅ Available" if status['openai'] else "❌ Unavailable"
    vision_status = "✅ Available" if status['vision'] else "❌ Unavailable"
    whisper_status = "✅ Available" if status['whisper'] else "❌ Unavailable"

    return (
        f"🧠 *AI Status:*\n\n"
        f"🤖 OpenAI GPT: {openai_status}\n"
        f"🖼️ Vision API: {vision_status}\n"
        f"🎤 Whisper: {whisper_status}"
    )


def format_context_for_openai(context_history: List[Dict]) -> List[Dict]:
    """Formats conversation history for OpenAI."""
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
