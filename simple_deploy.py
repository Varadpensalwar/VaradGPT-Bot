#!/usr/bin/env python3
"""
Simple deployment entry point for VaradGPT Bot
Minimal dependencies and robust error handling
"""

import os
import sys
import asyncio

def main():
    """Simple deployment entry point"""
    print("Starting VaradGPT Bot...")
    
    # Check environment variables
    required_vars = ['OPENAI_API_KEY', 'TELEGRAM_BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your deployment platform's environment settings")
        sys.exit(1)
    
    print("Environment variables OK")
    
    # Import and run bot
    try:
        from main import on_startup, dispatcher, bot
        
        async def run_bot():
            print("Initializing bot...")
            await on_startup(dispatcher)
            print("Starting bot polling...")
            await dispatcher.start_polling(bot)
        
        asyncio.run(run_bot())
        
    except ImportError as e:
        print(f"ERROR: Failed to import bot modules: {e}")
        print("Make sure all required packages are installed")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 