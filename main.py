from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types, Router
import openai
import asyncio
from aiogram.filters import Command
from aiogram.types import BotCommand, FSInputFile, BufferedInputFile
import aiohttp
import json
from geopy.geocoders import Nominatim
from aiogram.fsm.storage.memory import MemoryStorage
import re
from rapidfuzz import fuzz, process
import logging


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("DEBUG: openai.api_key =", openai.api_key, "TELEGRAM_BOT_TOKEN =", TELEGRAM_BOT_TOKEN)
if not openai.api_key or not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("OPENAI_API_KEY and TELEGRAM_BOT_TOKEN must be set in environment variables.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=openai.api_key)

# Safe getters (moved to top to avoid undefined errors)
def safe_user_id(message):
    return getattr(getattr(message, 'from_user', None), 'id', None)
def safe_full_name(message):
    return getattr(getattr(message, 'from_user', None), 'full_name', "Unknown")


class Reference:
    '''
    A class to store previously response from the openai API
    '''

    def __init__(self) -> None:
        self.response = ""



reference = Reference()
model_name = "gpt-4.1-nano"



# Initialize bot, dispatcher, and router
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dispatcher = Dispatcher(storage=storage)
router = Router()



def clear_past():
    """A function to clear the previous conversation and context.
    """
    reference.response = ""



# In-memory user language store
user_languages = {}

# At the top of the file, after user_languages = {}
user_seen = set()

# Add at the top, after user_seen = set()
user_usage_count = {}

# Helper to get user's language, always returns 'en' if user_id is None or not a string
def get_lang(user_id):
    if not isinstance(user_id, str) and not isinstance(user_id, int):
        return 'en'
    return user_languages.get(user_id, 'en')

# Update all other handlers to use the selected language
@router.message(Command("clear"))
async def clear(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    clear_past()
    await message.reply("I've cleared the past conversation. Let's start fresh!")


# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Update /start handler ---
@router.message(Command("start"))
async def welcome(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    user = getattr(message, 'from_user', None)
    first_name = getattr(user, 'first_name', 'there')
    last_name = getattr(user, 'last_name', '')
    if last_name:
        full_name = f"{first_name} {last_name}"
    else:
        full_name = first_name
    # Returning user check
    if user_id in user_seen:
        await message.reply(f"Welcome back, {full_name}!")
    else:
        user_seen.add(user_id)
        await message.reply(f"""
Hello {full_name}!
Welcome to the VaradGPT!
How can I help you?
For quick use - /help
""")


@router.message(Command("help"))
async def helper(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    await message.reply("""
Hi There, I'm VaradGPT created by Varad Pensalwar! Please follow these commands for quick access - 
/start    - Start a new conversation
/clear    - Clear conversation history and context
/help     - Display this help menu
/about    - Learn about Varad and background information
/projects - View Varad's featured projects
/resume   - Access Varad's professional resume
/contact  - Get Varad's contact information
/website  - Visit Varad's personal portfolio
I hope this helps. :)
""")

@router.message(Command("about"))
async def about(message: types.Message):
    await message.reply(
        "🤖 About VaradGPT Bot & Owner\n\n"
        "VaradGPT is a conversational AI Telegram bot built using OpenAI's GPT models. It can answer questions, chat, and assist with various tasks.\n\n"
        "👤 Bot Owner: Varad\n"
        "I am Varad, the creator and maintainer of this bot. If you have questions, feedback, or want to collaborate, feel free to reach out!\n\n"
        "Features include:\n"
        "- get detail info about varad\n"
        "- integrated OpenAI llm model\n"
        "- Voice message support\n"
        "- And more!\n\n"
        "🔗 *Portfolio* - https://varadpensalwar.vercel.app/\n"
        "💻 *GitHub* - https://github.com/Varadpensalwar\n"
        "💼 *LinkedIn* - https://www.linkedin.com/in/varadpensalwar/\n"
        "🐦 *Twitter* - https://twitter.com/PensalwarVarad\n"
        "✉️ *Email* - varadpensalwar@gmail.com\n"
        "📱 *Mobile* - +91 - 8669580734\n",
        parse_mode="Markdown", disable_web_page_preview=True
    )

@router.message(Command("contact"))
async def send_contact(message: types.Message):
    contact_text = (
        "Here's how you can connect with Varad Pensalwar:\n\n"
        "🔗 Website - https://varadpensalwar.vercel.app \n"
        "🐙 GitHub - https://github.com/Varadpensalwar \n"
        "💼 LinkedIn - https://www.linkedin.com/in/varadpensalwar \n"
        "🐦 Twitter - https://twitter.com/varadpensalwar \n"
        "✉️ Email: varadpensalwar@gmail.com\n"
        
    )
    await message.reply(contact_text, parse_mode="Markdown")
    vcard_path = "VaradPensalwar.vcf"
    if os.path.exists(vcard_path):
        await message.answer_document(FSInputFile(vcard_path, filename='VaradPensalwar.vcf'), caption="📇 Varad Pensalwar – vCard")

@router.message(Command("project"))
async def project_info(message: types.Message):
    await message.reply(
        """
*Here are some of Varad's featured projects:*

"""
        "*DocMind*\n"
        "DocMind is an AI-powered PDF information retrieval system that enables users to quickly extract insights from their documents using advanced language models and semantic vector search. With a user-friendly Streamlit web interface, DocMind supports multi-PDF uploads, natural language Q&A, and intelligent document retrieval—making it ideal for researchers, students, and professionals.\n"
        "[GitHub](https://github.com/Varadpensalwar/DocMind) | [Live Demo](https://docmind-varad-pensalwar.streamlit.app/)\n\n"
        "*HealthAI-Assistant*\n"
        "HealthAI-Assistant is a medical chatbot that leverages AI to provide health-related information based on medical literature. The application uses a Retrieval-Augmented Generation (RAG) approach to answer user queries by referencing a medical knowledge base.\n"
        "[GitHub](https://github.com/Varadpensalwar/HealthAI-Assistant.git) | [Demo](https://drive.google.com/file/d/1MyUsry_0wvEu-DcefOTXk-ZXc_rUrHoW/view)\n\n"
        "*VaradGPT Bot*\n"
        "VaradGPT Bot is a friendly, AI-powered Telegram bot built with Python and OpenAI GPT, offering natural conversational AI, voice message transcription, birthday reminders, and festive greetings. Designed for seamless interaction, it leverages aiogram, OpenAI APIs, and other modern Python libraries to deliver a rich chat experience.\n"
        "[GitHub](https://github.com/Varadpensalwar/VaradGPT-Bot) | [Try on Telegram](https://t.me/VaradGPTBot)\n\n"
        , parse_mode="Markdown", disable_web_page_preview=True
    )

@router.message(Command("projects"))
async def projects_info(message: types.Message):
    await project_info(message)

@router.message(lambda m: m.voice is not None)
async def handle_voice(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    file_id = getattr(getattr(message, 'voice', None), 'file_id', None)
    if not file_id:
        await message.reply("Voice file not found.")
        return
    file = await bot.get_file(file_id)
    file_path = getattr(file, 'file_path', None)
    if not file_path:
        await message.reply("Voice file path not found.")
        return
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
    ogg_path = f"voice_{user_id}.ogg"
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            with open(ogg_path, 'wb') as f:
                f.write(await resp.read())
    # Transcribe using OpenAI Whisper
    transcription = None
    try:
        with open(ogg_path, 'rb') as audio_file:
            transcript_resp = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            transcription = transcript_resp.text
    except Exception as e:
        await message.reply("Sorry, I couldn't transcribe your voice message.")
        os.remove(ogg_path)
        return
    os.remove(ogg_path)
    await message.reply(f"Transcription: {transcription}")
    # Send transcription to ChatGPT
    prev_response = reference.response if reference.response else ""
    try:
        safe_text = transcription if isinstance(transcription, str) else ""
        response = client.chat.completions.create(
            model = model_name,
            messages = [
                {"role": "assistant", "content": prev_response},
                {"role": "user", "content": f"""{safe_text}

Please provide a helpful, clear, and engaging response in English. Follow these guidelines:
- Keep your response to 2 concise paragraphs maximum
- Be conversational and natural in tone
- Directly address the user's question or topic
- Provide specific, actionable information when possible
- If the topic is complex, focus on the most important points
- Use examples or analogies if they help clarify your explanation
- Avoid unnecessary jargon or overly technical language unless specifically requested
- Do not answer about medical reated query answer until you are 100%, always tell to take advice from doctors
- if you did not have latest info then do not create hypothetical or fake content, directly say sorry, i do not have enough info about this topic"""}
            ]
        )
        chatgpt_reply = response.choices[0].message.content
        if chatgpt_reply:
            reference.response = chatgpt_reply
        print(f">>> chatGPT: \n\t{reference.response}")
        await bot.send_message(chat_id = message.chat.id, text = reference.response)
    except Exception as e:
        await message.reply("Sorry, I couldn't get a response from ChatGPT.")
        print(f"OpenAI error: {e}")
        return








# Move these handlers above the catch-all
@router.message(Command("resume"))
async def send_resume(message: types.Message):
    import os
    summary = (
        "*Varad Pensalwar – Resume Summary*\n\n"
        "🎓 *Education*: B.Tech in Artificial Intelligence & Machine Learning, Sanjay Ghodawat University, Kolhapur\n"
        "💼 *Experience*: AI/ML Engineer, GenAI Specialist\n"
        "🚀 *Key Projects*: VaradGPT Bot, DocMind, BookSense, and more.\n\n"
        "For full details, see my attached resume.\n"
        "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
        "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
        "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
        "✉️ Email: varadpensalwar@gmail.com\n"
    )
    await message.reply(summary, parse_mode="Markdown")
    # Prefer a pre-uploaded file ID if provided to avoid file-system issues in some deployments
    resume_file_id = os.getenv('RESUME_FILE_ID')
    if resume_file_id:
        await bot.send_document(chat_id=message.chat.id, document=resume_file_id, caption="📄 Varad Pensalwar – Resume")
    else:
        resume_path = os.path.join(os.path.dirname(__file__), 'Varad_Pensalwar_Resume.pdf')
        if os.path.exists(resume_path):
            with open(resume_path, "rb") as f:
                data = f.read()
            input_file = BufferedInputFile(data, filename="Varad_Pensalwar_Resume.pdf")
            await bot.send_document(
                chat_id=message.chat.id,
                document=input_file,
                caption="📄 Varad Pensalwar – Resume"
            )
        else:
            # Fallback to sending via URL (GitHub raw file or RESUME_URL env)
            resume_url = os.getenv('RESUME_URL', 'https://raw.githubusercontent.com/Varadpensalwar/VaradGPT-Bot/main/Varad_Pensalwar_Resume.pdf')
            await bot.send_document(
                chat_id=message.chat.id,
                document=resume_url,
                caption="📄 Varad Pensalwar – Resume"
            )


@router.message(Command("website"))
async def send_website(message: types.Message):
    await message.reply(
        "🔗 *Varad Pensalwar's* Personal Portfolio:\n" 
        "🔗 *Website* - https://varadpensalwar.vercel.app",
        parse_mode="Markdown"
    )

# Ensure the catch-all handler remains at the end
@router.message()
async def chatgpt(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    
    # Track usage count (session only)
    user_usage_count[user_id] = user_usage_count.get(user_id, 0) + 1
    user_text = message.text.lower() if message.text else ""
    
   
    
    # If not a bot-specific query, use LLM for general questions
    await handle_general_question(message, user_id)
 

async def handle_general_question(message, user_id):
    """Handle general questions using the LLM"""
    prev_response = reference.response if reference.response else ""
    safe_text = message.text if isinstance(message.text, str) else ""
    
    if not safe_text.strip():
        await message.reply("Please send a valid message.")
        return
    
    try:
        response = client.chat.completions.create(
            model = model_name,
            messages = [
                {"role": "assistant", "content": prev_response},
                {"role": "user", "content": safe_text + "\nPlease answer in English. Limit your response to no more than two concise paragraphs."}
            ]
        )
        chatgpt_reply = response.choices[0].message.content
        if chatgpt_reply:
            reference.response = chatgpt_reply
        print(f">>> chatGPT: \n\t{reference.response}")
        await bot.send_message(chat_id = message.chat.id, text = reference.response)
    except Exception as e:
        await message.reply("Sorry, I couldn't get a response from ChatGPT.")
        print(f"OpenAI error: {e}")
        return

# Register the router in the dispatcher
async def on_startup(dispatcher: Dispatcher):
    dispatcher.include_router(router)
    await set_bot_commands(bot)

# Remove /groupinfo from the bot command menu
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the conversation"),
        BotCommand(command="help", description="Show help menu"),
        BotCommand(command="about", description="About VaradGPT Bot & owner"),
        BotCommand(command="project", description="Show Varad's featured projects"),
        BotCommand(command="resume", description="View Varad's resume (PDF)"),
        BotCommand(command="contact", description="Contact Varad (links, email & Mob.)"),
        BotCommand(command="website", description="View Varad's personal website/portfolio"),
        BotCommand(command="clear", description="Clear conversation/context"),
    ]
    await bot.set_my_commands(commands)

if __name__ == "__main__":
    async def main():
        await on_startup(dispatcher)
        await dispatcher.start_polling(bot)
    asyncio.run(main())


