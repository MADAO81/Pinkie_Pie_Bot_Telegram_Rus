import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes  # <-- ДОБАВЬТЕ ЭТО
)
from bot.config import Config
from bot.handlers.commands import (
    start,
    help_command,
    recipe_command,
    joke_command,
    song_command,
    weather_command,
    subscribe_command,
    unsubscribe_command
)
from bot.handlers.messages import handle_message
from bot.handlers.photos import handle_photo
from bot.handlers.voice import handle_voice
from bot.core.scheduler import start_scheduler
from bot.core.constants import VERSION
