# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (for gtts, geopy, ffmpeg, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables (optional, can be set in Railway dashboard)
# ENV OPENAI_API_KEY=your-key
# ENV TELEGRAM_BOT_TOKEN=your-token

# Run the bot
CMD ["python", "main.py"] 