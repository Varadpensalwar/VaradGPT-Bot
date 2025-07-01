from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types, Router
import openai
import sys
import asyncio
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, InputFile, FSInputFile
import gspread
from google.oauth2.service_account import Credentials as SACredentials
from datetime import datetime
import aiohttp
from gtts import gTTS
from pydub import AudioSegment
import pytz
import json
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from aiohttp import web
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()
openai.api_key = os.getenv("OpenAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not openai.api_key or not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("OPENAI_API_KEY and TELEGRAM_BOT_TOKEN must be set in environment variables.")


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



# Language dictionaries
LANGUAGES = {
    'en': {
        'welcome': "Hi\nI am VaradGPT Bot! Created by Varad Pensalwar. How can I assist you?",
        'help': """
Hi There, I'm VaradGPT Bot created by Varad Pensalwar! Please follow these commands - 
/start - to start the conversation
/clear - to clear the past conversation and context.
/help - to get this help menu.
/language - to change language.
I hope this helps. :)
""",
        'cleared': "I've cleared the past conversation and context.",
        'choose_language': "Please choose your language:",
        'language_set': "Language set to English.",
        'about': """
🤖 *VaradGPT Bot*\nCreated by Varad Pensalwar\nPowered by OpenAI GPT\nLanguages: English, Hindi, Marathi\nSource: [GitHub](https://github.com/VaradPensalwar)\n""",
    },
    'hi': {
        'welcome': "नमस्ते\nमैं वरदजीपीटी बोट हूँ! वरद पेंसालवार द्वारा निर्मित। मैं आपकी कैसे सहायता कर सकता हूँ?",
        'help': """
नमस्ते, मैं वरद पेंसालवार द्वारा बनाया गया वरदजीपीटी बोट हूँ! कृपया ये कमांड्स आज़माएँ - 
/start - बातचीत शुरू करने के लिए
/clear - पिछली बातचीत और संदर्भ साफ़ करने के लिए
/help - यह सहायता मेनू पाने के लिए
/language - भाषा बदलने के लिए
आशा है यह मदद करेगा :)
""",
        'cleared': "मैंने पिछली बातचीत और संदर्भ साफ़ कर दिया है।",
        'choose_language': "कृपया अपनी भाषा चुनें:",
        'language_set': "भाषा हिंदी पर सेट की गई है।",
        'about': """
🤖 *वरदजीपीटी बोट*\nनिर्माता: वरद पेंसालवार\nOpenAI GPT द्वारा संचालित\nभाषाएँ: अंग्रे़ी, हिंदी, मराठी\nस्रोत: [GitHub](https://github.com/VaradPensalwar)\n""",
    },
    'mr': {
        'welcome': "नमस्कार\nमी वरदजीपीटी बोट आहे! वरद पेंसालवार यांनी तयार केले आहे. मी तुम्हाला कशी मदत करू शकतो?",
        'help': """
नमस्कार, मी वरद पेंसालवार यांनी तयार केलेला वरदजीपीटी बोट आहे! कृपया हे कमांड्स वापरा - 
/start - संभाषण सुरू करण्यासाठी
/clear - मागील संभाषण आणि संदर्भ साफ करण्यासाठी
/help - ही मदत मेनू मिळवण्यासाठी
/language - भाषा बदलण्यासाठी
आशा आहे हे उपयुक्त ठरेल :)
""",
        'cleared': "मी मागील संभाषण आणि संदर्भ साफ केले आहेत.",
        'choose_language': "कृपया आपली भाषा निवडा:",
        'language_set': "भाषा मराठीवर सेट केली आहे.",
        'about': """
🤖 *वरदजीपीटी बोट*\nनिर्माता: वरद पेंसालवार\nOpenAI GPT द्वारे समर्थित\nभाषा: इंग्रजी, हिंदी, मराठी\nस्रोत: [GitHub](https://github.com/VaradPensalwar)\n""",
    }
}

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

# /language command handler
@router.message(Command("language"))
async def language_command(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="English")],
            [KeyboardButton(text="हिंदी")],
            [KeyboardButton(text="मराठी")],
        ],
        resize_keyboard=True
    )
    lang = get_lang(user_id)
    await message.reply(LANGUAGES[lang]['choose_language'], reply_markup=kb)

# Language selection handler
@router.message(lambda m: m.text in ["English", "हिंदी", "मराठी"])
async def set_language(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    lang_map = {"English": "en", "हिंदी": "hi", "मराठी": "mr"}
    user_text = message.text if isinstance(message.text, str) else "English"
    if user_text not in lang_map:
        user_text = "English"
    user_languages[user_id] = lang_map[user_text]
    await message.reply(LANGUAGES[lang_map[user_text]]['language_set'], reply_markup=types.ReplyKeyboardRemove())

# Update all other handlers to use the selected language
@router.message(Command("clear"))
async def clear(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    clear_past()
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
    await message.reply(LANGUAGES[lang]['cleared'])

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
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
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
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
    await message.reply(LANGUAGES[lang]['help'])

@router.message(Command("about"))
async def about(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
    await message.reply(LANGUAGES[lang]['about'], parse_mode="Markdown")

@router.message(Command("feedback"))
async def feedback_command(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
    awaiting_feedback.add(user_id)
    await message.reply(LANGUAGES[lang]['feedback_prompt'])

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'varadgpt-bot.json'
SPREADSHEET_ID = '1hBvCg8xMtOgTG84_dbRqVpa8cdrDeX6Tvffal2TGCe4'

# The following is for Google Sheets service account only (not related to Gmail user OAuth)
creds = SACredentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)  # type: ignore
gs_client = gspread.authorize(creds)
gs_sheet = gs_client.open_by_key(SPREADSHEET_ID).sheet1

# Update feedback handler to log to Google Sheets
@router.message(lambda m: safe_user_id(m) in awaiting_feedback)
async def handle_feedback(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
    try:
        await bot.send_message(chat_id=ADMIN_USER_ID, text=f"Feedback from {safe_full_name(message)} (id: {user_id}):\n{message.text}")
        # Log feedback to Google Sheets
        gs_sheet.append_row([
            str(user_id),
            str(safe_full_name(message)),
            str(message.text),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    except Exception as e:
        print(f"Failed to send feedback: {e}")
    awaiting_feedback.remove(user_id)
    await message.reply(LANGUAGES[lang]['feedback_thanks'])

@router.message(lambda m: m.voice is not None)
async def handle_voice(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
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
            transcript_resp = openai.Audio.transcribe("whisper-1", audio_file)
            if isinstance(transcript_resp, dict):
                transcription = transcript_resp.get('text', '')
            else:
                transcription = ''
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
        response = openai.ChatCompletion.create(
            model = model_name,
            messages = [
                {"role": "assistant", "content": prev_response},
                {"role": "user", "content": safe_text + "\nPlease answer in English."}
            ]
        )
        if isinstance(response, dict) and 'choices' in response and response['choices']:
            chatgpt_reply = response['choices'][0]['message']['content']
        else:
            await message.reply("Sorry, I couldn't get a valid response from ChatGPT.")
            return
    except Exception as e:
        await message.reply("Sorry, I couldn't get a response from ChatGPT.")
        return
    reference.response = chatgpt_reply
    print(f">>> chatGPT: \n\t{reference.response}")
    await bot.send_message(chat_id = message.chat.id, text = reference.response)

# Update admin/group chat ID for feedback
ADMIN_USER_ID = -4842086049  # Feedback will be sent to this group

# Track users waiting to send feedback
awaiting_feedback = set()

# Add feedback prompts to LANGUAGES
def add_feedback_langs():
    LANGUAGES['en']['feedback_prompt'] = "Please type your feedback and send it."
    LANGUAGES['en']['feedback_thanks'] = "Thank you for your feedback!"
    LANGUAGES['hi']['feedback_prompt'] = "कृपया अपनी प्रतिक्रिया लिखें और भेजें।"
    LANGUAGES['hi']['feedback_thanks'] = "आपकी प्रतिक्रिया के लिए धन्यवाद!"
    LANGUAGES['mr']['feedback_prompt'] = "कृपया आपली प्रतिक्रिया लिहा आणि पाठवा."
    LANGUAGES['mr']['feedback_thanks'] = "आपल्या प्रतिक्रियेबद्दल धन्यवाद!"
add_feedback_langs()

# Add group info command to LANGUAGES
def add_groupinfo_langs():
    LANGUAGES['en']['groupinfo'] = "This command shows info about the group."
    LANGUAGES['hi']['groupinfo'] = "यह कमांड ग्रुप की जानकारी दिखाता है।"
    LANGUAGES['mr']['groupinfo'] = "ही कमांड ग्रुपची माहिती दर्शवते."
add_groupinfo_langs()

@router.message(Command("groupinfo"))
async def groupinfo(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    lang = get_lang(user_id)
    if lang not in LANGUAGES:
        lang = 'en'
    if getattr(message.chat, 'type', None) in ["group", "supergroup"]:
        info = f"Group Name: {getattr(message.chat, 'title', 'Unknown')}\nGroup ID: {getattr(message.chat, 'id', 'Unknown')}"
        try:
            count = await bot.get_chat_member_count(message.chat.id)
            info += f"\nMembers: {count}"
        except Exception:
            pass
        await message.reply(info)
    else:
        await message.reply(LANGUAGES[lang]['groupinfo'])

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

# Move the catch-all handler to the end of the file
# --- Update chatgpt handler for time/date questions ---
@router.message()
async def chatgpt(message: types.Message):
    user_id = safe_user_id(message)
    if user_id is None:
        await message.reply("User not found.")
        return
    # Track usage count (session only)
    user_usage_count[user_id] = user_usage_count.get(user_id, 0) + 1
    user_text = message.text.lower() if message.text else ""
    # --- Time/Date Q&A: always reply with no real-time access ---
    if any(kw in user_text for kw in ["what time", "current time", "time is it", "what date", "current date", "date is it", "today", "day is it"]):
        await message.reply("As a bot, I do not have real-time access to date and time. You can check it on your device or preferred source.")
        return
    # --- Timezone setup: user says 'my timezone is <city/country>' ---
    if user_text.startswith("my timezone is "):
        location = user_text.replace("my timezone is ", "").strip()
        user_cities[str(user_id)] = location
        save_user_cities()
        await message.reply(f"Your city/timezone has been set to: {location}")
        return
    # --- Time/Date Q&A ---
    import re
    time_city_match = re.search(r'what time is it in ([\w\s,\-]+)\??', user_text)
    date_city_match = re.search(r'what day is it in ([\w\s,\-]+)\??', user_text)
    city = None
    if time_city_match:
        city = time_city_match.group(1).strip()
    elif date_city_match:
        city = date_city_match.group(1).strip()
    else:
        city = user_cities.get(str(user_id))
    # Handle 'what is my timezone' and 'what is today' and 'what day is it'
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
                # Only date part
                if isinstance(time_str, str):
                    date_part = time_str.split()[0]
                    await message.reply(f"Today in {zone_name} is {date_part}")
                else:
                    await message.reply("Sorry, I couldn't get the date for that city/timezone.")
        else:
            await message.reply("Sorry, I couldn't get the current time for that city/timezone. Please check the city name or try another.")
        return
    # --- Personal Q&A ---
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
            # Fallback to local calculation
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
    if "what is my user id" in user_text or "my user id" in user_text or "who am i" in user_text:
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
            # Fallback to local calculation
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            await message.reply(f"Today is {now.strftime('%A, %d %B %Y')} (your timezone: {tz_name})")
        return
    if "how many times have i used" in user_text or "usage count" in user_text or "how many times" in user_text:
        count = user_usage_count.get(user_id, 1)
        await message.reply(f"You have used this bot {count} times in this session.")
        return
    prev_response = reference.response if reference.response else ""
    safe_text = message.text if isinstance(message.text, str) else ""
    if not safe_text.strip():
        await message.reply("Please send a valid message.")
        return
    try:
        response = openai.ChatCompletion.create(
            model = model_name,
            messages = [
                {"role": "assistant", "content": prev_response},
                {"role": "user", "content": safe_text + "\nPlease answer in English."}
            ]
        )
        if isinstance(response, dict) and 'choices' in response and response['choices']:
            chatgpt_reply = response['choices'][0]['message']['content']
        else:
            await message.reply("Sorry, I couldn't get a valid response from ChatGPT.")
            return
    except Exception as e:
        await message.reply("Sorry, I couldn't get a response from ChatGPT.")
        return
    reference.response = chatgpt_reply
    print(f">>> chatGPT: \n\t{reference.response}")
    await bot.send_message(chat_id = message.chat.id, text = reference.response)

# Register the router in the dispatcher
async def on_startup(dispatcher: Dispatcher):
    dispatcher.include_router(router)
    await set_bot_commands(bot)

# Remove /groupinfo from the bot command menu
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the conversation"),
        BotCommand(command="help", description="Show help menu"),
        BotCommand(command="about", description="About VaradGPT Bot"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="clear", description="Clear conversation/context"),
        BotCommand(command="feedback", description="Send feedback to the creator"),
        BotCommand(command="groupinfo", description="Group info"),
    ]
    await bot.set_my_commands(commands)

# Safe getters
def safe_user_id(message):
    return getattr(getattr(message, 'from_user', None), 'id', None)
def safe_full_name(message):
    return getattr(getattr(message, 'from_user', None), 'full_name', "Unknown")

if __name__ == "__main__":
    async def main():
        await on_startup(dispatcher)
        await dispatcher.start_polling(bot)
    asyncio.run(main())


