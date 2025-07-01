import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# print(TELEGRAM_BOT_TOKEN)

#configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message_handler(commands=['start', 'help'])
async def command_start_handler(message: types.Message):
    """
    This handler receives messages with `/start` or  `/help `command
    """
    await message.reply("Hi\nI am VaradGPT Bot!\nPowered by Varad Pensalwar.")



@dp.message_handler()
async def echo(message: types.Message):
    """
    This will retrun echo
    """
    await message.answer(message.text)


# Register handlers in a setup function
async def on_startup(dp: Dispatcher):
    dp.message.register(command_start_handler, commands={"start", "help"})
    dp.message.register(echo)


if __name__ == "__main__":
    async def main():
        await on_startup(dp)
        await dp.start_polling(bot)
    asyncio.run(main())

