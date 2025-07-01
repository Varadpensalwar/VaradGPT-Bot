# VaradGPT Bot 🤖

A friendly, AI-powered Telegram bot built with Python and OpenAI GPT, featuring timezone and city utilities, voice message transcription, and a customizable user experience.

---

## ✨ Features

- **Conversational AI**: Powered by OpenAI GPT for natural, context-aware chat.
- **Timezone & City Utilities**: Users can set their city/timezone and get local time/date info.
- **Voice Message Transcription**: Converts Telegram voice messages to text using OpenAI Whisper.
- **Birthday Reminders**: Users can set and be greeted on their birthday.
- **Festive Greetings**: Sends special greetings on holidays and festivals.
- **English-only, clean, and privacy-friendly**: No language selection, no feedback logging, and no external data storage.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+
- **Frameworks/Libraries**:
  - [aiogram](https://docs.aiogram.dev/) (Telegram Bot API)
  - [openai](https://github.com/openai/openai-python) (ChatGPT/Whisper)
  - [gtts](https://pypi.org/project/gTTS/) (Text-to-Speech)
  - [pydub](https://github.com/jiaaro/pydub) (Audio processing)
  - [python-dotenv](https://pypi.org/project/python-dotenv/) (Env management)
  - [pytz](https://pypi.org/project/pytz/) (Timezone support)
  - [timezonefinder](https://pypi.org/project/timezonefinder/) (City to timezone)
  - [geopy](https://pypi.org/project/geopy/) (Geocoding)
  - [aiohttp](https://docs.aiohttp.org/) (Async HTTP)

---

## 📁 Project Structure

```text
VaradGPT-Bot/
├── LICENSE
├── main.py
├── README.md
├── requirements.txt
├── runtime.txt
├── research/
│   └── varadgpt_bot.py
├── varadgptbot/
│   └── (virtual environment files)
```

---

## ⚙️ Installation & Setup

### **Prerequisites**
- Python 3.12+
- Telegram account (to create a bot via [BotFather](https://core.telegram.org/bots#botfather))
- OpenAI account & API key

### **1. Clone the repository**
```bash
git clone https://github.com/Varadpensalwar/VaradGPT-Bot.git
cd VaradGPT-Bot
```

### **2. Create and activate a virtual environment**
```bash
python -m venv varadgptbot
# On Windows:
./varadgptbot/Scripts/activate
# On macOS/Linux:
source varadgptbot/bin/activate
```

### **3. Install dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set up environment variables**
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your-openai-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

---

## 🚀 Running the Bot

### **Development**
```bash
python main.py
```

### **Production (Render/Railway/Other)**
- Ensure `runtime.txt` specifies `python-3.12.3` for compatibility.
- Set environment variables in your deployment dashboard.
- Use the start command:
  ```bash
  python main.py
  ```

---

## 📝 Contributing

Contributions are welcome! To contribute:
1. Fork the repo
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋‍♂️ Contact & Support

- **Author:** Varad Pensalwar
- **GitHub:** [Varadpensalwar](https://github.com/Varadpensalwar)
- **Telegram:** [@Varadpensalwar](https://t.me/Varadpensalwar)
- **Issues:** [GitHub Issues](https://github.com/Varadpensalwar/VaradGPT-Bot/issues)

---

> _Happy coding and chatting with VaradGPT Bot!_ 