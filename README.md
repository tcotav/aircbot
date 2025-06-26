# AircBot

A simple IRC bot that automatically captures and saves links shared in channels.

## Features

- Connects to IRC channels and monitors messages
- Automatically detects and saves shared links
- Fetches link metadata (title, description)
- Stores links in SQLite database with deduplication
- Provides commands to search and browse saved links
- Simple memory system for conversation context

## Quick Start

1. **Install dependencies:**
   ```bash
   ./start.sh  # This will set up everything automatically
   ```
   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure the bot:**
   ```bash
   cp .env.example .env
   # Edit .env with your IRC server details
   ```

3. **Test the bot (optional):**
   ```bash
   python demo.py  # See bot functionality without connecting to IRC
   ```

4. **Run the bot:**
   ```bash
   ./start.sh  # Or: source venv/bin/activate && python bot.py
   ```

## Configuration

Edit the `.env` file with your settings:

- `IRC_SERVER` - IRC server address (default: irc.libera.chat)
- `IRC_PORT` - IRC server port (default: 6667)
- `IRC_NICKNAME` - Bot's nickname
- `IRC_CHANNEL` - Channel to join (include # prefix)
- `IRC_PASSWORD` - Bot's password (if required)
- `DATABASE_PATH` - Path to SQLite database file

## Commands

- `!links` - Show recent links
- `!links search <term>` - Search saved links
- `!links stats` - Show statistics
- `!help` - Show help information

## Database Schema

The bot creates two tables:

### links
- `id` - Primary key
- `url` - The saved URL
- `title` - Page title
- `description` - Page description
- `user` - Who shared the link
- `channel` - Which channel it was shared in
- `timestamp` - When it was saved

### messages
- `id` - Primary key
- `user` - Message author
- `channel` - Channel name
- `message` - Message content
- `timestamp` - When it was sent

## Development

The bot is structured in modular components:

- `bot.py` - Main IRC bot logic
- `database.py` - Database operations
- `link_handler.py` - URL detection and metadata fetching
- `config.py` - Configuration management

## Example Usage

Once running, the bot will automatically save any links shared in the channel:

```
<user> Check out this cool project: https://github.com/example/repo
<aircbot> 📎 Saved: Example Repository - A cool project

<user> !links
<aircbot> 📚 Recent links:
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> !links search github
<aircbot> 🔍 Search results for 'github':
<aircbot> • Example Repository (by user) - https://github.com/example/repo
```

## Requirements

- Python 3.7+
- Internet connection for fetching link metadata
- Access to IRC server
