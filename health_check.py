#!/usr/bin/env python3
"""
Health check endpoint for deployment platforms
This provides a simple web server that deployment platforms can use to verify the service is running
"""

import os
import asyncio
from aiohttp import web
import logging

logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "VaradGPT Bot",
        "message": "Bot is running successfully"
    })

async def start_bot():
    """Start the bot in the background"""
    try:
        from main import on_startup, dispatcher, bot
        await on_startup(dispatcher)
        # Start bot polling in background
        asyncio.create_task(dispatcher.start_polling(bot))
        logger.info("Bot started successfully in background")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

async def init_app():
    """Initialize the web application"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    # Start bot when app starts
    app.on_startup.append(lambda app: asyncio.create_task(start_bot()))
    
    return app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8080))
    
    # Start web server
    web.run_app(init_app(), port=port, host='0.0.0.0') 