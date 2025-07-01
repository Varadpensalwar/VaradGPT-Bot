# VaradGPT Bot 🤖

A multilingual, AI-powered Telegram bot built with Python and OpenAI GPT, featuring Google Sheets integration, timezone and city utilities, and a friendly, customizable user experience.

---

## ✨ Features

- **Conversational AI**: Powered by OpenAI GPT for natural, context-aware chat.
- **Multilingual Support**: English, Hindi, and Marathi out of the box.
- **Google Sheets Feedback Logging**: User feedback is logged directly to a Google Sheet.
- **Timezone & City Utilities**: Users can set their city/timezone and get local time/date info.
- **Voice Message Transcription**: Converts Telegram voice messages to text using OpenAI Whisper.
- **Personalization**: Remembers user language, birthday, and usage count.
- **Group Info**: Provides group chat statistics and info.
- **Easy Extensibility**: Modular codebase for adding new commands and features.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, [aiogram](https://docs.aiogram.dev/), [OpenAI API](https://platform.openai.com/docs/api-reference), [gspread](https://gspread.readthedocs.io/en/latest/)
- **Utilities**: [python-dotenv](https://pypi.org/project/python-dotenv/), [pytz](https://pypi.org/project/pytz/), [timezonefinder](https://pypi.org/project/timezonefinder/), [geopy](https://geopy.readthedocs.io/en/stable/), [Babel](https://babel.pocoo.org/)
- **Deployment**: Render, Docker, or any Python-friendly cloud/VPS

---

## 📁 Project Structure

```plaintext
VaradGPT-Bot/
├── main.py                  # Main bot application
├── requirements.txt         # Python dependencies
├── .gitignore               # Files/folders to ignore in git
├── LICENSE                  # MIT License
├── research/
│   └── varadgpt_bot.py      # Experimental/legacy bot code
├── varadgptbot/             # Python virtual environment (do not commit)
│   ├── Lib/
│   ├── Scripts/
│   ├── Include/
│   └── pyvenv.cfg
└── varadgpt-bot.json        # Google service account credentials (DO NOT COMMIT)
```

---

## 🚦 Prerequisites

- Python 3.8+
- Telegram account (to create a bot via [BotFather](https://core.telegram.org/bots#botfather))
- OpenAI API key ([get one here](https://platform.openai.com/account/api-keys))
- Google Cloud service account with Sheets API enabled ([guide](https://gspread.readthedocs.io/en/latest/oauth2.html))
- (Optional) Render, Heroku, or VPS for deployment

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Varadpensalwar/VaradGPT-Bot.git
   cd VaradGPT-Bot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv varadgptbot
   # On Windows:
   .\varadgptbot\Scripts\activate
   # On macOS/Linux:
   source varadgptbot/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env` and fill in your secrets:
     ```env
     TELEGRAM_BOT_TOKEN=your-telegram-bot-token
     OPENAI_API_KEY=your-openai-api-key
     ```

5. **Add Google service account credentials**
   - Download your `varadgpt-bot.json` from Google Cloud and place it in the project root.
   - **Never commit this file!**

---

## 📝 Environment Variables

Create a `.env` file in your project root:

```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPENAI_API_KEY=your-openai-api-key
```

---

## 🚀 Running the Bot

### Development

```bash
python main.py
```

### Production (Render/Heroku)

- Set environment variables and upload `varadgpt-bot.json` as a secret file in your platform's dashboard.
- Use the following start command:
  ```bash
  python main.py
  ```

---

## 🤝 Contributing

Contributions are welcome!  
Please open an issue or submit a pull request for new features, bug fixes, or improvements.

**How to contribute:**
1. Fork the repo
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to your branch (`git push origin feature/your-feature`)
5. Open a pull request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 💬 Contact & Support

- **Author:** Varad Pensalwar
- **GitHub:** [Varadpensalwar](https://github.com/Varadpensalwar)
- **Telegram:** [@VaradPensalwar](https://t.me/VaradPensalwar)
- **Issues:** [GitHub Issues](https://github.com/Varadpensalwar/VaradGPT-Bot/issues)

---

## 🙏 Acknowledgements

- [aiogram](https://docs.aiogram.dev/)
- [OpenAI](https://openai.com/)
- [gspread](https://gspread.readthedocs.io/en/latest/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [timezonefinder](https://pypi.org/project/timezonefinder/)
- [geopy](https://geopy.readthedocs.io/en/stable/)
- [Babel](https://babel.pocoo.org/)

---

> **Enjoy building with VaradGPT Bot! 🚀** 