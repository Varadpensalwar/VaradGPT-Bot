# Deployment Guide for VaradGPT Bot

This guide will help you deploy your VaradGPT Bot on various platforms like Render, Railway, Heroku, and others.

## 🚀 Quick Deployment Options

### Option 1: Simple Bot Deployment (Recommended)
Use `deploy.py` for platforms that support long-running processes:
- **Procfile**: `web: python deploy.py`
- **Best for**: Render, Railway, DigitalOcean App Platform

### Option 2: Web Server with Health Check
Use `health_check.py` for platforms that expect web servers:
- **Procfile**: `web: python health_check.py`
- **Best for**: Heroku, Google Cloud Run, AWS Elastic Beanstalk

## 📋 Prerequisites

1. **Environment Variables Required**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather

2. **Python Version**: 3.12.3 (specified in `runtime.txt`)

## 🔧 Platform-Specific Instructions

### Render.com

1. **Connect your GitHub repository**
2. **Create a new Web Service**
3. **Configure the service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python deploy.py`
   - **Environment Variables**:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
4. **Deploy**

### Railway.app

1. **Connect your GitHub repository**
2. **Create a new service**
3. **Configure environment variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
4. **Deploy** (Railway will auto-detect the Procfile)

### Heroku

1. **Install Heroku CLI and login**
2. **Create a new app**:
   ```bash
   heroku create your-app-name
   ```
3. **Set environment variables**:
   ```bash
   heroku config:set OPENAI_API_KEY=your-openai-api-key
   heroku config:set TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   ```
4. **Deploy**:
   ```bash
   git push heroku main
   ```

### DigitalOcean App Platform

1. **Connect your GitHub repository**
2. **Create a new app**
3. **Configure**:
   - **Source**: Your GitHub repo
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python deploy.py`
4. **Add environment variables** and deploy

## 🛠️ Troubleshooting

### Common Issues

1. **"No open ports detected"**
   - This is normal for Telegram bots using polling
   - Use `health_check.py` if your platform requires a web server

2. **Environment variables not found**
   - Make sure to set them in your platform's dashboard
   - Don't rely on `.env` files for production

3. **Bot not responding**
   - Check logs for errors
   - Verify your bot token is correct
   - Ensure only one instance is running

4. **OpenAI API errors**
   - Verify your API key is correct
   - Check your OpenAI account has sufficient credits
   - Ensure you're using the correct model name

### Debugging Steps

1. **Check logs** in your deployment platform's dashboard
2. **Verify environment variables** are set correctly
3. **Test locally** first with `python main.py`
4. **Check bot status** by messaging @BotFather

## 📝 Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | ✅ |
| `PORT` | Port for web server (auto-set by platforms) | ❌ |

## 🔄 Updating Your Bot

1. **Push changes** to your GitHub repository
2. **Redeploy** on your platform (usually automatic)
3. **Check logs** to ensure successful deployment

## 📞 Support

If you encounter issues:
1. Check the logs in your deployment platform
2. Verify all environment variables are set
3. Test the bot locally first
4. Check the [main README](README.md) for more details

---

**Happy deploying! 🚀** 