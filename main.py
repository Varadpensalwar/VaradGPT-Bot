from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types, Router
import openai
import sys
import asyncio
from aiogram.filters import Command
from aiogram.types import BotCommand, InputFile, FSInputFile
import aiohttp
from gtts import gTTS
import pytz
import json
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from aiohttp import web
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import re
from rapidfuzz import fuzz, process

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
model_name = "gpt-4o-mini"



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
    await message.reply("I've cleared the past conversation and context.")

def get_timezone_from_lang_code(lang_code):
    # Map common language codes to timezones
    mapping = {
        'en-US': 'America/New_York',
        'en-GB': 'Europe/London',
        'en-IN': 'Asia/Kolkata',
        'hi-IN': 'Asia/Kolkata',
        'mr-IN': 'Asia/Kolkata',
        'de-DE': 'Europe/Berlin',
        'fr-FR': 'Europe/Paris',
        'es-ES': 'Europe/Madrid',
        'es-MX': 'America/Mexico_City',
        'ru-RU': 'Europe/Moscow',
        'zh-CN': 'Asia/Shanghai',
        'ja-JP': 'Asia/Tokyo',
        # Add more as needed
    }
    if not lang_code:
        return 'UTC'
    # Try full code first
    if lang_code in mapping:
        return mapping[lang_code]
    # Try just the country part
    if '-' in lang_code:
        country = lang_code.split('-')[1]
        for code, tz in mapping.items():
            if code.endswith(country):
                return tz
    return 'UTC'

# --- Birthday storage ---
BIRTHDAY_FILE = 'birthdays.json'
if os.path.exists(BIRTHDAY_FILE):
    with open(BIRTHDAY_FILE, 'r') as f:
        user_birthdays = json.load(f)
else:
    user_birthdays = {}

def save_birthdays():
    with open(BIRTHDAY_FILE, 'w') as f:
        json.dump(user_birthdays, f)

# --- Festive greetings dictionary (expand as needed) ---
FESTIVE_DAYS = {
    'Asia/Kolkata': {
        '01-01': '🎉 Happy New Year! 🎉',
        '15-08': '🇮🇳 Happy Independence Day! 🇮🇳',
        '25-12': '🎄 Merry Christmas! 🎄',
    },
    'America/New_York': {
        '01-01': '🎉 Happy New Year! 🎉',
        '04-07': '🇺🇸 Happy Independence Day! 🇺🇸',
        '25-12': '🎄 Merry Christmas! 🎄',
    },
    'Europe/London': {
        '01-01': '🎉 Happy New Year! 🎉',
        '25-12': '🎄 Merry Christmas! 🎄',
    },
    # Add more as needed
}

# --- /birthday command handler ---
@router.message(Command("birthday"))
async def set_birthday(message: types.Message):
    user_id = str(safe_user_id(message))
    if not isinstance(message.text, str):
        await message.reply("Could not read your message. Please use the format: /birthday DD-MM (e.g., /birthday 15-08)")
        return
    args = message.text.split()
    if len(args) == 2:
        bday = args[1]
        # Validate format DD-MM
        try:
            day, month = map(int, bday.split('-'))
            if 1 <= day <= 31 and 1 <= month <= 12:
                user_birthdays[user_id] = bday
                save_birthdays()
                await message.reply(f"Your birthday has been set to {bday}. 🎂")
                return
        except Exception:
            pass
        await message.reply("Please use the format: /birthday DD-MM (e.g., /birthday 15-08)")
    else:
        # Show current birthday if set
        bday = user_birthdays.get(user_id)
        if bday:
            await message.reply(f"Your birthday is set to {bday}. 🎂 To change it, use /birthday DD-MM")
        else:
            await message.reply("Please set your birthday using: /birthday DD-MM (e.g., /birthday 15-08)")

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
    # Time-based greeting using user's language_code
    lang_code = getattr(user, 'language_code', None)
    tz_name = get_timezone_from_lang_code(lang_code)
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    hour = now.hour
    weekday = now.strftime('%A')
    today_str = now.strftime('%d-%m')
    # Birthday greeting
    bday_greeting = None
    if str(user_id) in user_birthdays and user_birthdays[str(user_id)] == today_str:
        bday_greeting = f"🎂 Happy Birthday, {first_name}! 🎉\n"
    # Festive greeting
    festive_greeting = None
    if tz_name in FESTIVE_DAYS and today_str in FESTIVE_DAYS[tz_name]:
        festive_greeting = FESTIVE_DAYS[tz_name][today_str] + "\n"
    # Returning user check
    if user_id in user_seen:
        welcome_line = f"Welcome back, {first_name}!"
    else:
        welcome_line = f"Welcome, {first_name}!"
        user_seen.add(user_id)
    greeting = (
        f"{bday_greeting or ''}{festive_greeting or ''}{welcome_line} 👋\n"
        "I'm VaradGPT Bot, your personal AI assistant.\n"
        "How can I help you today?"
    )
    await message.reply(greeting)

@router.message(Command("help"))
async def helper(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    await message.reply("""
Hi There, I'm VaradGPT Bot created by Varad Pensalwar! Please follow these commands - 
/start - to start the conversation
/clear - to clear the past conversation and context.
/help - to get this help menu.
I hope this helps. :)
""")

@router.message(Command("about"))
async def about(message: types.Message):
    await message.reply(
        "🤖 *About VaradGPT Bot & Owner*\n\n"
        "VaradGPT is a conversational AI Telegram bot built using OpenAI's GPT models. It can answer questions, chat, and assist with various tasks.\n\n"
        "👤 *Bot Owner*: Varad\n"
        "I am Varad, the creator and maintainer of this bot. If you have questions, feedback, or want to collaborate, feel free to reach out!\n\n"
        "Features include:\n"
        "- Natural language conversation\n"
        "- Birthday and timezone features\n"
        "- Voice message support\n"
        "- And more!\n\n"
        "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
        "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
        "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
        "✉️ Email: varadpensalwar@gmail.com\n"
    )

@router.message(Command("project"))
async def project_info(message: types.Message):
    await message.reply(
        """
*Here are some of Varad's featured projects:*

"""
        "*DocMind*\n"
        "DocMind is an AI-powered PDF information retrieval system that enables users to quickly extract insights from their documents using advanced language models and semantic vector search. With a user-friendly Streamlit web interface, DocMind supports multi-PDF uploads, natural language Q&A, and intelligent document retrieval—making it ideal for researchers, students, and professionals.\n"
        "[GitHub](https://github.com/Varadpensalwar/DocMind) | [Live Demo](https://docmind-varad-pensalwar.streamlit.app/)\n\n"
        "*BookSense*\n"
        "BookSense is an AI-powered semantic book recommender that helps users discover books matching their interests, categories, and emotional tone using advanced NLP and vector search. With a modern Gradio dashboard, BookSense enables natural language queries, emotion and category filtering, and instant recommendations.\n"
        "[GitHub](https://github.com/Varadpensalwar/BookSense) | [Demo](https://drive.google.com/file/d/1MyUsry_0wvEu-DcefOTXk-ZXc_rUrHoW/view)\n\n"
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
- Avoid unnecessary jargon or overly technical language unless specifically requested"""}
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

# --- User timezone storage ---
USER_TZ_FILE = 'user_timezones.json'
if os.path.exists(USER_TZ_FILE):
    with open(USER_TZ_FILE, 'r') as f:
        user_timezones = json.load(f)
else:
    user_timezones = {}

def save_user_timezones():
    with open(USER_TZ_FILE, 'w') as f:
        json.dump(user_timezones, f)

tzfinder = TimezoneFinder()

# Helper to get user's timezone
def get_user_timezone(user_id, lang_code=None):
    user_id = str(user_id)
    if user_id in user_timezones:
        return user_timezones[user_id]
    # Try to guess from lang_code
    tz_name = get_timezone_from_lang_code(lang_code)
    if tz_name == 'UTC':
        return None
    return tz_name

# Helper to get current time and date from WorldTimeAPI
async def get_time_for_timezone(tz_name):
    url = f'https://worldtimeapi.org/api/timezone/{tz_name}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Example datetime: '2023-07-02T18:30:00.000000+05:30'
                    dt = data.get('datetime')
                    tz = data.get('timezone')
                    if dt and tz:
                        # Format: Sunday, 02 July 2023 18:30:00
                        from datetime import datetime
                        dt_obj = datetime.fromisoformat(dt[:-6])
                        return dt_obj.strftime('%A, %d %B %Y %H:%M:%S'), tz
    except Exception:
        pass
    return None, None

# --- User city storage ---
USER_CITY_FILE = 'user_cities.json'
if os.path.exists(USER_CITY_FILE):
    with open(USER_CITY_FILE, 'r') as f:
        user_cities = json.load(f)
else:
    user_cities = {}

def save_user_cities():
    with open(USER_CITY_FILE, 'w') as f:
        json.dump(user_cities, f)

TIMEZONEDB_API_KEY = '9O6VYOJZWRL6'

# Helper to get time from TimeZoneDB
async def get_time_for_city(city):
    # Try to get lat/lon from city using geopy
    geolocator = Nominatim(user_agent="varadgpt-bot")
    loc = await asyncio.get_event_loop().run_in_executor(None, geolocator.geocode, city)
    if loc is not None and not asyncio.iscoroutine(loc) and hasattr(loc, 'latitude') and hasattr(loc, 'longitude'):
        lat, lon = loc.latitude, loc.longitude
        url = f'http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONEDB_API_KEY}&format=json&by=position&lat={lat}&lng={lon}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == 'OK':
                            time_str = data.get('formatted')  # e.g. '2025-07-02 18:30:00'
                            zone_name = data.get('zoneName')
                            gmt_offset = data.get('gmtOffset')
                            return time_str, zone_name, gmt_offset
        except Exception:
            pass
    return None, None, None

# --- /setcity command handler ---
@router.message(Command("setcity"))
async def set_city(message: types.Message):
    user_id = str(safe_user_id(message))
    if not isinstance(message.text, str):
        await message.reply("Could not read your message. Please use the format: /setcity <your city or timezone>")
        return
    args = message.text.split(maxsplit=1)
    if len(args) == 2:
        city = args[1].strip()
        user_cities[user_id] = city
        save_user_cities()
        await message.reply(f"Your city/timezone has been set to: {city}")
    else:
        city = user_cities.get(user_id)
        if city:
            await message.reply(f"Your city/timezone is set to: {city}. To change it, use /setcity <your city or timezone>")
        else:
            await message.reply("Please set your city or timezone using: /setcity <your city or timezone>")

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
    resume_path = os.path.join(os.path.dirname(__file__), 'Varad_Pensalwar_Resume.pdf')
    try:
        # Use bot.send_document for broader compatibility across aiogram versions
        await bot.send_document(chat_id=message.chat.id, document=FSInputFile(resume_path, filename='Varad_Pensalwar_Resume.pdf'), caption="📄 Varad Pensalwar – Resume")
    except Exception as e:
        # Send a brief error message to the user and log to stdout for debugging
        await message.reply("❌ Sorry, I couldn't send the resume right now.")
        print(f"ERROR sending resume: {e} (path={resume_path})")

@router.message(Command("cv"))
async def send_cv(message: types.Message):
    await send_resume(message)

# Add a regex-based handler for /resume and /cv with extra words
@router.message(lambda m: isinstance(m.text, str) and re.match(r"^/(resume|cv)\b", m.text.lower()))
async def send_resume_regex(message: types.Message):
    await send_resume(message)

# Ultra-flexible resume/cv/portfolio handler (natural language, regex-based)
@router.message(lambda m: isinstance(m.text, str) and re.search(
    r'(?i)(/)?(resume|resumé|cv|curricul[au]m vitae|portfolio|portfolyo|profile|bio|background|experience|education|journey|career|work)[^a-z]*'
    r'(varad|pensalwar|your|you|bot|owner|admin|creator|author|maintainer|developer|founder)?', m.text))
async def send_resume_natural(message: types.Message):
    await send_resume(message)

# Ultra-flexible owner/creator/admin handler (regex-based)
@router.message(lambda m: isinstance(m.text, str) and re.search(
    r'(?i)(who (is )?(the )?(owner|creator|maker|admin|author|maintainer|developer|founder|builder|created|built|make|made)|owner|creator|maker|admin|author|maintainer|developer|founder|built|made|make|created)( of (this|the|varadgpt|bot|project|service|assistant|application|code|software|platform|system|solution|product|tool))?', m.text))
async def send_owner_info(message: types.Message):
    await message.reply(
        "Varad Pensalwar is the owner, creator, and maintainer of this bot and several other AI projects.\n\n"
        "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
        "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
        "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
        "✉️ Email: varadpensalwar@gmail.com\n"
    )

# 4. About Varad Handler (move above Q&A handler)
@router.message(lambda m: isinstance(m.text, str) and (
    re.search(r'(?i)(about|abotu|abot|abou|bio|profile|background|info|details|story|journey|who is|who\'s|who are|tell me|describe|introduce|introduction|summary|summarize)', m.text) and
    re.search(r'(?i)(varad|you|his|her|their|the owner\'s|the creator\'s|the admin\'s|the maintainer\'s|the developer\'s|the founder\'s)', m.text) and
    not any(p in m.text.lower() for p in ["resume", "cv", "project", "projects"])
))
async def send_varad_info_intent(message: types.Message):
    await message.reply(
        "Varad Pensalwar is an AI/ML Engineer and GenAI Specialist from Pune, India. He is passionate about building intelligent systems that transform reality. Varad is the creator and maintainer of this bot and several other AI projects.\n\n"
        "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
        "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
        "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
        "✉️ Email: varadpensalwar@gmail.com\n"
    )

# 5. Q&A About Varad Handler (typo-tolerant, intent-based)
qa_pairs = {
    "favorite programming language": "Python!",
    "what inspires": "Building things that help people, AI progress, and curiosity.",
    "hobbies": "Chess, Coding, reading, exploring AI, music, and travel.",
    "mission": "To push the boundaries of AI and make technology accessible and helpful for everyone.",
    "where are you from": "Pune, Maharashtra, India 🇮🇳",
    "educational background": "B.Tech in Artificial Intelligence & Machine Learning from Sanjay Ghodawat University, Kolhapur.",
    "favorite ai technology": "Large Language Models (LLMs) and Generative AI!",
    "dream project": "Building an AI assistant that can truly understand and help people in their daily lives.",
    "favorite book": "Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph by Mayo Oshin & Nuno Campos.",
    "favorite quote": "The future belongs to those who understand AI.",
    "favorite chess opening": "The Queen's Gambit!",
    "programming languages": "Python, SQL, and a bit of JavaScript.",
    "favorite open-source project": "HuggingFace Transformers.",
    "relax": "Listening to music and playing chess.",
    "github": "[Varadpensalwar](https://github.com/Varadpensalwar)",
    "linkedin": "[linkedin.com/in/varadpensalwar](https://www.linkedin.com/in/varadpensalwar/)",
    "twitter": "[@PensalwarVarad](https://twitter.com/PensalwarVarad)",
    "favorite ai application": "Conversational AI bots and creative AI tools.",
    "favorite tech in gen ai": "LangChain.",
    "favorite sport": "Chess!",
    "favorite food": "Indian cuisine, especially paneer dishes.",
    "favorite place": "Sydney, Australia.",
    "favorite music genre": "Classical and instrumental.",
    "long-term goal": "To lead impactful AI projects and contribute to the global AI community.",
    "favorite movie": "My favorite movie is Bloody Daddy!",
    "favorite programming framework": "I love working with FastAPI for building modern web APIs.",
    "favorite ide or code editor": "My go-to code editor is VS Code for its versatility and extensions.",
    "favorite holiday destination": "Sydney, Australia is my favorite holiday destination!",
    "favorite startup or tech company": "I admire Google and Atlassian for their innovation and impact.",
    "favorite productivity tool": "Notion and Cursor are my favorite productivity tools for organizing work and ideas.",
    "favorite youtube channel or podcast": "I enjoy learning from Code With Harry on YouTube.",
    "favorite color": "Orange is my favorite color—it's vibrant and energetic!",
    "favorite animal": "The tiger is my favorite animal, symbolizing strength and courage.",
    "favorite subject in school": "Math was always my favorite subject.",
    "favorite way to learn new things": "I love learning from official documentation—it's the most reliable source!",
    "favorite ai use case": "I love using AI for solving bugs and making development smoother.",
    "favorite thing about being an ai/ml engineer": "Watching code transform raw data into intelligent insights that nobody has ever seen before is the best part of being an AI/ML engineer.",
    "website": "🔗 [Website](https://varadpensalwar.vercel.app/)",
    "portfolio": "You can explore my portfolio and learn more about me at 🔗 [Website](https://varadpensalwar.vercel.app/)",
    "personal website": "My personal website is 🔗 [Website](https://varadpensalwar.vercel.app/)",
}

def is_varad_qa_question(m):
    if not isinstance(m.text, str):
        return False
    # Exclude generic identity questions
    identity_phrases = ["who are you", "who is varad", "who am i", "who's", "who is the owner", "who is the creator"]
    if any(phrase in m.text.lower() for phrase in identity_phrases):
        return False
    return any(fuzz.partial_ratio(m.text.lower(), q) >= 80 for q in qa_pairs.keys())

@router.message(is_varad_qa_question)
async def send_varad_qa(message: types.Message):
    # Find the best match
    if not isinstance(message.text, str):
        return
    best_q, score, _ = process.extractOne(message.text.lower(), qa_pairs.keys(), scorer=fuzz.partial_ratio)
    if score >= 80:
        answer = qa_pairs[best_q]
        # If the question is about portfolio, website, or background, append the website link if not present
        if best_q in ["portfolio", "website", "personal website", "background", "about", "bio"] and "varadpensalwar.vercel.app" not in answer:
            answer += "\n🔗 [Website](https://varadpensalwar.vercel.app/)"
        await message.reply(answer)

# Contact Card Handler (robust, typo-tolerant, intent-based)
def is_contact_request(m):
    if not isinstance(m.text, str):
        return False
    contact_words = [
        "contact", "email", "phone", "connect", "reach", "information", "details", "how to contact", "how to reach", "how to connect", "get in touch", "address", "social", "whatsapp", "telegram"
    ]
    context_words = [
        "varad", "owner", "creator", "him", "his", "their", "pensalwar", "bot"
    ]
    text = m.text.lower()
    # typo-tolerant: match if any contact word is close and any context word is present
    if any(fuzz.partial_ratio(word, cw) >= 80 for word in text.split() for cw in contact_words) and any(ctx in text for ctx in context_words):
        return True
    # also match if both a contact word and a context word appear anywhere in the text
    if any(cw in text for cw in contact_words) and any(ctx in text for ctx in context_words):
        return True
    return False

@router.message(is_contact_request)
async def send_contact_intent(message: types.Message):
    contact_text = (
        "Here's how you can connect with Varad Pensalwar:\n\n"
        "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
        "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
        "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
        "✉️ Email: varadpensalwar@gmail.com\n"
    )
    await message.reply(contact_text, parse_mode="Markdown")
    vcard_path = "VaradPensalwar.vcf"
    if os.path.exists(vcard_path):
        await message.answer_document(FSInputFile(vcard_path, filename='VaradPensalwar.vcf'), caption="📇 Varad Pensalwar – vCard")

# 1. Resume/CV/Portfolio Handler (add negative check for identity questions)
@router.message(lambda m: isinstance(m.text, str) and (
    any(fuzz.partial_ratio(word, kw) >= 85 for word in m.text.lower().split() for kw in ["resume", "cv", "curriculum vitae", "portfolio", "profile", "bio", "background", "experience", "education", "journey", "career", "work"]) and
    any(ctx in m.text.lower() for ctx in ["varad", "pensalwar", "your", "you", "bot", "owner", "admin", "creator", "author", "maintainer", "developer", "founder", "his", "her", "their", "the owner's", "the creator's", "the admin's", "the maintainer's", "the developer's", "the founder's"]) and
    not any(p in m.text.lower() for p in ["project", "projects"]) and
    not any(phrase in m.text.lower() for phrase in ["who are you", "who is varad", "who am i", "who's", "who is the owner", "who is the creator"])
))
async def send_resume_intent(message: types.Message):
    await send_resume(message)

@router.message(Command("contact"))
async def send_contact(message: types.Message):
    contact_text = (
        "Here's how you can connect with Varad Pensalwar:\n\n"
        "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
        "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
        "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
        "✉️ Email: varadpensalwar@gmail.com\n"
    )
    await message.reply(contact_text, parse_mode="Markdown")
    vcard_path = "VaradPensalwar.vcf"
    if os.path.exists(vcard_path):
        await message.answer_document(FSInputFile(vcard_path, filename='VaradPensalwar.vcf'), caption="📇 Varad Pensalwar – vCard")

@router.message(Command("website"))
async def send_website(message: types.Message):
    await message.reply(
        "🔗 Varad Pensalwar's personal website/portfolio:\n🔗 [Website](https://varadpensalwar.vercel.app/)",
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
    
    # Check if this is a bot-specific query first
    if is_bot_specific_query(user_text):
        await handle_bot_specific_query(message, user_text, user_id)
        return
    
    # If not a bot-specific query, use LLM for general questions
    await handle_general_question(message, user_id)

def is_bot_specific_query(user_text):
    """Check if the query is specifically about the bot, Varad, or bot features"""
    
    # Bot-specific keywords
    bot_keywords = [
        # Varad/owner related
        "varad", "pensalwar", "owner", "creator", "developer", "founder", "admin", "maintainer",
        "who made", "who built", "who created", "who developed", "who is behind",
        
        # Bot features
        "my birthday", "my timezone", "my name", "my user id", "my language", "usage count",
        "what is my", "when is my", "how many times",
        
        # Commands and features
        "resume", "cv", "portfolio", "contact", "website", "project", "projects",
        "skills", "tech stack", "expertise", "about varad", "about you",
        
        # Greetings
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "namaste", "yo", "sup",
        
        # Time/date queries (bot handles these)
        "what time", "current time", "time is it", "what date", "current date", "date is it", "today", "day is it",
        "my timezone is"
    ]
    
    return any(keyword in user_text for keyword in bot_keywords)

async def handle_bot_specific_query(message, user_text, user_id):
    """Handle queries specifically about the bot, Varad, or bot features"""
    
    # Resume/CV/Portfolio handlers
    resume_keywords = [
        "resume", "cv", "curriculum vitae", "portfolio", "profile", "bio", "background",
        "experience", "education", "journey", "career", "work"
    ]
    context_keywords = [
        "varad", "pensalwar", "your", "you", "bot", "owner", "admin", "creator",
        "author", "maintainer", "developer", "founder"
    ]
    
    def fuzzy_in(text, keywords, threshold=85):
        return any(fuzz.partial_ratio(text, kw) >= threshold for kw in keywords)
    
    user_text_words = user_text.split()
    for word in user_text_words:
        if fuzzy_in(word, resume_keywords) and any(ctx in user_text for ctx in context_keywords):
            await send_resume(message)
            return
        if fuzzy_in(word, context_keywords) and any(rk in user_text for rk in resume_keywords):
            await send_resume(message)
            return
    
    # Creator/owner handler
    creator_keywords = [
        "who made", "who build", "who built", "who is your creator", "who is your developer", 
        "who is your founder", "who is your owner", "who is your maker", "who is behind you", 
        "who created you", "who is the author", "who programmed you", "who is responsible for you", 
        "who is varadgpt's creator", "who is the person behind this bot", "who is the maintainer", 
        "who is the admin", "who is the mastermind", "who is the architect", "who is the engineer", 
        "who is the builder", "who developed you"
    ]
    if any(kw in user_text for kw in creator_keywords):
        await message.reply(
            "I was created and maintained by Varad Pensalwar (AI/ML Engineer and GenAI Specialist).\n"
            "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
            "🔗 GitHub: https://github.com/Varadpensalwar\n"
            "🔗 LinkedIn: https://www.linkedin.com/in/varadpensalwar/\n"
            "🔗 Twitter: https://twitter.com/PensalwarVarad"
        )
        return
    
    # Timezone setup
    if user_text.startswith("my timezone is "):
        location = user_text.replace("my timezone is ", "").strip()
        user_cities[str(user_id)] = location
        save_user_cities()
        await message.reply(f"Your city/timezone has been set to: {location}")
        return
    
    # Time/Date queries
    time_city_match = re.search(r'what time is it in ([\w\s,\-]+)\??', user_text)
    date_city_match = re.search(r'what day is it in ([\w\s,\-]+)\??', user_text)
    city = None
    if time_city_match:
        city = time_city_match.group(1).strip()
    elif date_city_match:
        city = date_city_match.group(1).strip()
    else:
        city = user_cities.get(str(user_id))
    
    if ("what is my timezone" in user_text or "my timezone" in user_text or
        "what is today" in user_text or "what day is it" in user_text or
        time_city_match or date_city_match):
        if not city:
            await message.reply("I couldn't detect your city/timezone. Please set it using /setcity <your city or timezone> or ask e.g. 'What time is it in New York?'")
            return
        time_str, zone_name, gmt_offset = await get_time_for_city(city)
        if time_str:
            if "time" in user_text:
                await message.reply(f"The current time in {zone_name} is {time_str} (GMT offset: {gmt_offset})")
            else:
                if isinstance(time_str, str):
                    date_part = time_str.split()[0]
                    await message.reply(f"Today in {zone_name} is {date_part}")
                else:
                    await message.reply("Sorry, I couldn't get the date for that city/timezone.")
        else:
            await message.reply("Sorry, I couldn't get the current time for that city/timezone. Please check the city name or try another.")
        return
    
    # Personal Q&A
    if any(kw in user_text for kw in ["when is my birthday", "what is my birthday", "birthday date", "my birthday", "birthday?"]):
        bday = user_birthdays.get(str(user_id))
        if bday:
            await message.reply(f"Your birthday is set to {bday}. 🎂")
        else:
            await message.reply("I don't know your birthday yet. Please set it using /birthday DD-MM (e.g., /birthday 15-08)")
        return
    
    if "what is my name" in user_text or "who am i" in user_text:
        user = getattr(message, 'from_user', None)
        first_name = getattr(user, 'first_name', '')
        last_name = getattr(user, 'last_name', '')
        if last_name:
            full_name = f"{first_name} {last_name}"
        else:
            full_name = first_name
        await message.reply(f"Your name is {full_name}.")
        return
    
    if "what is my timezone" in user_text or "my timezone" in user_text:
        user = getattr(message, 'from_user', None)
        lang_code = getattr(user, 'language_code', None)
        tz_name = get_user_timezone(user_id, lang_code)
        if not tz_name:
            await message.reply("I couldn't detect your timezone. Please tell me your country or city by sending: my timezone is <your city/country>")
            return
        dt_str, tz = await get_time_for_timezone(tz_name)
        if dt_str:
            await message.reply(f"Your timezone is: {tz}\nCurrent local time: {dt_str}")
        else:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            await message.reply(f"Your timezone is: {tz_name}\nCurrent local time: {now.strftime('%A, %d %B %Y %H:%M:%S')}")
        return
    
    if "what is my language" in user_text or "my language" in user_text:
        user = getattr(message, 'from_user', None)
        lang_code = getattr(user, 'language_code', None)
        lang = get_lang(user_id)
        await message.reply(f"Your Telegram language code is: {lang_code}\nThe bot is currently using: {lang}")
        return
    
    if "what is my user id" in user_text or "my user id" in user_text:
        await message.reply(f"Your Telegram user ID is: {user_id}")
        return
    
    if "what is today" in user_text or "what day is it" in user_text:
        user = getattr(message, 'from_user', None)
        lang_code = getattr(user, 'language_code', None)
        tz_name = get_user_timezone(user_id, lang_code)
        if not tz_name:
            await message.reply("I couldn't detect your timezone. Please tell me your country or city by sending: my timezone is <your city/country>")
            return
        dt_str, tz = await get_time_for_timezone(tz_name)
        if dt_str:
            await message.reply(f"Today is {dt_str.split()[0]}, {dt_str.split()[1]} {dt_str.split()[2]} {dt_str.split()[3]} (your timezone: {tz})")
        else:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            await message.reply(f"Today is {now.strftime('%A, %d %B %Y')} (your timezone: {tz_name})")
        return
    
    if "how many times have i used" in user_text or "usage count" in user_text or "how many times" in user_text:
        count = user_usage_count.get(user_id, 1)
        await message.reply(f"You have used this bot {count} times in this session.")
        return
    
    # Project info handler
    project_keywords = ["project", "projects"]
    context_keywords = [
        "your", "you", "varad", "bot", "about", "show", "list", "tell", "demo", "work", "portfolio", 
        "created", "built", "developed", "made", "feature", "featuring", "examples", "sample", 
        "my", "our", "owner", "author", "maintainer"
    ]
    if any(pk in user_text for pk in project_keywords) and any(ck in user_text for ck in context_keywords):
        await project_info(message)
        return
    
    # Skills/tech stack handler
    skills_keywords = ["skills", "tech stack", "technology", "technologies", "languages", "tools", 
                      "expertise", "specialization", "speciality", "what can you do", "what are you good at", "what do you know"]
    if any(kw in user_text for kw in skills_keywords):
        await message.reply(
            "I'm Varad Pensalwar, an AI/ML Engineer and GenAI Specialist.\n"
            "My expertise includes: Machine Learning, Deep Learning (CNNs, RNNs, Transformers, GANs), Generative AI (LLMs, Diffusion Models), Computer Vision, NLP, Agentic AI, MLOps, and more.\n"
            "I work with Python, R, SQL, TensorFlow, PyTorch, HuggingFace, LangChain, FastAPI, Docker, and more.\n\n"
            "See my full profile and projects:\n"
            "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
            "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
            "🔗 [Twitter](https://twitter.com/PensalwarVarad)"
        )
        return
    
    # Contact/social handler
    contact_keywords = ["contact", "connect", "reach", "email", "social", "how to contact", 
                       "how to reach", "how to connect", "get in touch"]
    if any(kw in user_text for kw in contact_keywords):
        await message.reply(
            "You can connect with Varad Pensalwar here:\n"
            "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
            "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
            "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
            "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
            "Or email: varadpensalwar@gmail.com"
        )
        return
    
    # Greeting handler
    greeting_keywords = [
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon", 
        "good evening", "namaste", "yo", "sup"
    ]
    greeting_pattern = re.compile(
        r"^\s*(" + "|".join(re.escape(greet) for greet in greeting_keywords) + r")[\s!.,]*$",
        re.IGNORECASE
    )
    if greeting_pattern.match(user_text):
        await message.reply(
            "Hello! 👋 I'm VaradGPT Bot, your personal AI assistant.\n"
            "You can ask me about Varad's projects, skills, or how to contact him.\n"
            "Try commands like /about or /project, or just ask in your own words!"
        )
        return
    
    # About Varad handler
    varad_keywords = [
        "who is varad", "tell me about varad", "about varad", "varad pensalwar", "who is varad pensalwar", 
        "varad's profile", "varad's bio", "varad's background", "varad's info",
        "who are you", "who is the owner", "who is the admin", "who is the founder", "who is the mastermind", 
        "who is the genius behind this", "who is the architect", "who is the engineer", "who is the builder", 
        "who maintains this bot", "who runs this bot", "who is behind this bot", "who is the person behind this bot", 
        "who is the creator of this bot", "who is the author of this bot", "who developed this bot",
        "who is varadgpt", "varadgpt owner", "varadgpt creator", "varadgpt admin", "varadgpt author", 
        "varadgpt maintainer", "varadgpt developer", "varadgpt founder", "varadgpt background", "varadgpt bio", "varadgpt info",
        "who made this bot", "who built this bot", "who is responsible for this bot", "who is the genius behind varadgpt", 
        "who is the mastermind behind varadgpt", "who is the developer of varadgpt", "who is the engineer of varadgpt", 
        "who is the architect of varadgpt", "who is the admin of varadgpt", "who is the maintainer of varadgpt", 
        "who is the owner of varadgpt", "who is the founder of varadgpt", "who is the creator of varadgpt"
    ]
    if any(kw in user_text for kw in varad_keywords):
        await message.reply(
            "Varad Pensalwar is an AI/ML Engineer and GenAI Specialist from Pune, India. He is passionate about building intelligent systems that transform reality. Varad is the creator and maintainer of this bot and several other AI projects.\n\n"
            "🔗 [Website](https://varadpensalwar.vercel.app/)\n"
            "🔗 [GitHub](https://github.com/Varadpensalwar)\n"
            "🔗 [LinkedIn](https://www.linkedin.com/in/varadpensalwar/)\n"
            "🔗 [Twitter](https://twitter.com/PensalwarVarad)\n"
            "✉️ Email: varadpensalwar@gmail.com\n"
        )
        return
    
    # Resume/CV/Portfolio handler
    resume_words = [
        "resume", "cv", "curriculum vitae", "portfolio", "profile", "bio", "background", 
        "experience", "education", "journey", "career", "work"
    ]
    context_words = [
        "varad", "pensalwar", "your", "you", "bot", "owner", "admin", "creator", 
        "author", "maintainer", "developer", "founder"
    ]
    if any(rw in user_text for rw in resume_words) and any(cw in user_text for cw in context_words):
        await send_resume(message)
        return
    
    # If none of the above, it should have been handled by LLM
    # This should not be reached, but just in case
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
        BotCommand(command="contact", description="Contact Varad (links & email)"),
        BotCommand(command="website", description="View Varad's personal website/portfolio"),
        BotCommand(command="clear", description="Clear conversation/context"),
    ]
    await bot.set_my_commands(commands)

if __name__ == "__main__":
    async def main():
        await on_startup(dispatcher)
        await dispatcher.start_polling(bot)
    asyncio.run(main())


