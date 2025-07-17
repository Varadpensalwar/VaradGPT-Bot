import logging
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN must be present in environment variables(.env).")

#configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(commands=["start", "help"])
async def command_start_handler(message: types.Message):
    """
    This handler receives messages with `/start` or  `/help `command
    """
    await message.reply("Hi\nI am VaradGPT Bot!\nPowered by Varad Pensalwar.")

@router.message()
async def echo(message: types.Message):
    """
    This will retrun echo
    """
    if message.text:
        await message.answer(message.text)
    else:
        await message.answer("No text to echo.")

# Register handlers in a setup function
async def on_startup(dispatcher: Dispatcher):
    dispatcher.include_router(router)

if __name__ == "__main__":
    async def main():
        await on_startup(dp)
        await dp.start_polling(bot)
    asyncio.run(main())

