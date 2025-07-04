#!/bin/bash

# Discord Bot Startup Script
echo "Starting AircBot Discord..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with your Discord bot token:"
    echo "DISCORD_TOKEN=your_bot_token_here"
    echo ""
    echo "Get a token from: https://discord.com/developers/applications"
    exit 1
fi

# Check if discord.py is installed
$(dirname "$0")/venv/bin/python -c "import discord" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing discord.py..."
    $(dirname "$0")/venv/bin/pip install discord.py
fi

# Start the Discord bot
$(dirname "$0")/venv/bin/python simple_discord_bot.py
