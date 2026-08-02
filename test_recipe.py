import asyncio
from telegram.ext import Application
from bot.config import Config
from bot.core.scheduler import send_daily_recipe

async def test():
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    await send_daily_recipe(app)

asyncio.run(test())
