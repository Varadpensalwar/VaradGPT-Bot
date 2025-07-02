# VaradGPT Bot 🤖

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/github/license/Varadpensalwar/VaradGPT-Bot)
![Last Commit](https://img.shields.io/github/last-commit/Varadpensalwar/VaradGPT-Bot)

A friendly, AI-powered Telegram bot built with Python and OpenAI GPT, featuring voice message transcription, birthday reminders, and festive greetings.

---

## Table of Contents
- [Demo](#demo)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Running the Bot](#-running-the-bot)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact & Support](#-contact--support)

---
## Demo

<details>
<summary>📹 Click to watch demo video</summary>
<br>

https://github.com/Varadpensalwar/VaradGPT-Bot/blob/main/Demo.mp4

</details>

**Try the bot:**
- **Desktop/PC**: [Open in Telegram Web](https://web.telegram.org/k/#@VaradGPTBot)
- **Mobile**: [Open in Telegram App](https://t.me/VaradGPTBot)
---

## ✨ Features

- **Conversational AI**: Powered by OpenAI GPT for natural, context-aware chat.
- **Voice Message Transcription**: Converts Telegram voice messages to text using OpenAI Whisper.
- **Birthday Reminders**: Users can set and be greeted on their birthday.
- **Festive Greetings**: Sends special greetings on holidays and festivals.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+
- **Frameworks/Libraries**:
  - [aiogram](https://docs.aiogram.dev/) (Telegram Bot API)
  - [openai](https://github.com/openai/openai-python) (ChatGPT/Whisper)
  - [gtts](https://pypi.org/project/gTTS/) (Text-to-Speech)
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
- Ensure `runtime.txt` specifies `python-3.12.3` (or your desired 3.12.x version) for compatibility.
- **Set environment variables in your deployment dashboard. Do NOT rely on a .env file for secrets on Render.**
- Use the start command:
  ```bash
  python main.py
  ```

---

## 🛠️ Troubleshooting

- **TelegramConflictError:** Only one instance of the bot can run at a time. Make sure you are not running the bot locally and on Render at the same time.
- **Environment Variables Not Detected:** On Render, set your secrets in the dashboard, not in a .env file.
- **No open ports detected:** This is normal for a Telegram bot using polling. You do not need to specify a port unless you use webhooks or run a web server.

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
