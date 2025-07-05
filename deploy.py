#!/usr/bin/env python3
"""
Deployment entry point for VaradGPT Bot
This file provides better error handling and logging for deployment platforms
"""

import os
import sys
import logging
import asyncio

# Configure logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    # Try to load dotenv if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.info("python-dotenv not available, using system environment variables")
    
    required_vars = ['OPENAI_API_KEY', 'TELEGRAM_BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your deployment platform's environment settings")
        return False
    
    logger.info("All required environment variables are set")
    return True

async def main():
    """Main deployment entry point"""
    try:
        logger.info("Starting VaradGPT Bot deployment...")
        
        # Check environment variables
        if not check_environment():
            sys.exit(1)
        
        # Import main bot functionality with error handling
        try:
            from main import on_startup, dispatcher, bot
        except ImportError as e:
            logger.error(f"Failed to import bot modules: {e}")
            logger.error("Make sure all required packages are installed")
            sys.exit(1)
        
        logger.info("Initializing bot...")
        await on_startup(dispatcher)
        
        logger.info("Starting bot polling...")
        await dispatcher.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Check your environment variables and bot configuration")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 