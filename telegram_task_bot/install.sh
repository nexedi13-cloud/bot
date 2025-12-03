#!/bin/bash
# Installation script for Telegram Task Bot

echo "Installing dependencies for Telegram Task Bot..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "pip is not installed. Please install pip first."
    exit 1
fi

# Install required packages
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "Dependencies installed successfully!"
    echo "Now copy .env.example to .env and add your bot token:"
    echo "cp .env.example .env"
    echo "Then edit .env file with your bot token from @BotFather"
    echo ""
    echo "To run the bot:"
    echo "python bot.py"
else
    echo "Failed to install dependencies."
    exit 1
fi