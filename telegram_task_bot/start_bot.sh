#!/bin/bash
# Script to start the Telegram Task Bot

echo "Starting Telegram Task Bot..."

# Change to the bot directory
cd /workspace/telegram_task_bot

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with your bot token:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    exit 1
fi

# Check if the token is set in .env
if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "your_bot_token_here" .env; then
    echo "Error: TELEGRAM_BOT_TOKEN is not properly set in .env file!"
    echo "Please update the .env file with your actual bot token from @BotFather"
    exit 1
fi

# Start the bot
python bot.py