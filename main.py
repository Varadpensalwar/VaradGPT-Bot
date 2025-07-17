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
        "who is the builder", "who developed you", "who made?",
        "who made?", "who build?", "who built?", "who is your creator?", "who is your developer?", "who is your founder?", "who is your owner?", "who is your maker?", "who is behind you?", "who created you?", "who is the author?", "who programmed you?", "who is responsible for you?", "who is varadgpt's creator?", "who is the person behind this bot?", "who is the maintainer?", "who is the admin?", "who is the mastermind?", "who is the architect?", "who is the engineer?", "who is the builder?", "who developed you?"

    ]
    if any(kw in user_text for kw in creator_keywords):
        creator_text = (
        "I was created and maintained by Varad Pensalwar (AI/ML Engineer and GenAI Specialist).\n"
            "🔗 Website: https://varadpensalwar.vercel.app \n"
            "🔗 GitHub: https://github.com/Varadpensalwar\n"
            "🔗 LinkedIn: https://www.linkedin.com/in/varadpensalwar\n"
            "🔗 Twitter: https://twitter.com/PensalwarVarad"
        
    )
    await message.reply(creator_text, parse_mode="Markdown")
    

    
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
    

    
    if "what is my user id" in user_text or "my user id" in user_text:
        await message.reply(f"Your Telegram user ID is: {user_id}")
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
            "My expertise include: Developing AI Agents to Solve Real-World Problems. \n"
            "I work with Python, SQL, LangChain, RAG and more.\n\n"
            "See my full profile and projects:\n"
            "🐙 GitHub - https://github.com/Varadpensalwar\n"
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


