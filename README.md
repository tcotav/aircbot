# AircBot

A simple IRC bot that automatically captures and saves links shared in channels.

## Features

- **Automatic Link Detection**: Connects to IRC channels and monitors messages for links
- **Link Metadata**: Automatically fetches and stores link titles and descriptions  
- **Smart Deduplication**: Avoids saving duplicate links
- **Command Interface**: Traditional !commands for link management
- **Natural Language**: Responds to natural mentions like "bubba, show me the links"
- **LLM Integration**: Answers questions using locally hosted LLM (Ollama/OpenAI-compatible)
- **SSL Support**: Connects to IRC servers with SSL (including self-signed certificates)
- **Memory System**: Maintains conversation context for better LLM responses
- **Rate Limiting**: Prevents spam with configurable per-user and total request limits
- **Robust Logging**: Detailed connection and error logging without channel spam

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
   python test_suite.py          # Run all tests
   python test_suite.py --test rate  # Test specific component
   python demo.py               # See bot functionality without connecting to IRC
   ```

4. **Run the bot:**
   ```bash
   ./start.sh  # Or: source venv/bin/activate && python bot.py
   ```

## Configuration

Edit the `.env` file with your settings:

### IRC Settings
- `IRC_SERVER` - IRC server address (default: irc.libera.chat)
- `IRC_PORT` - IRC server port (default: 6667)  
- `IRC_NICKNAME` - Bot's nickname
- `IRC_CHANNEL` - Channel to join (include # prefix)
- `IRC_PASSWORD` - Bot's password (if required)
- `IRC_USE_SSL` - Enable SSL connection (true/false)
- `IRC_SSL_VERIFY` - Verify SSL certificates (false for self-signed)

### LLM Settings (for !ask command and mentions)
- `LLM_ENABLED` - Enable LLM features (true/false)
- `LLM_BASE_URL` - API endpoint (e.g., http://localhost:11434/v1 for Ollama)
- `LLM_API_KEY` - API key (use "ollama" for local Ollama)
- `LLM_MODEL` - Model name (e.g., deepseek-r1:latest)
- `LLM_MAX_TOKENS` - Maximum response length (default: 150)
- `LLM_TEMPERATURE` - Creativity level 0.0-1.0 (default: 0.7)

### Database
- `DATABASE_PATH` - Path to SQLite database file

### Rate Limiting  
- `RATE_LIMIT_USER_PER_MINUTE` - Max requests per user per minute (default: 1)
- `RATE_LIMIT_TOTAL_PER_MINUTE` - Max total requests per minute (default: 10)

## Commands

### Traditional Commands
- `!links` - Show recent links
- `!links search <term>` - Search saved links by keyword
- `!links by <user>` - Show links shared by specific user
- `!links stats` - Show link statistics 
- `!links details` - Show recent links with timestamps
- `!ask <question>` - Ask the LLM a question
- `!ratelimit` - Show rate limit status  
- `!help` - Show help information

### Natural Language (Bot Mentions)
You can also mention the bot by name and ask naturally:

**Link Requests:**
- `bubba, show me the links` → Shows recent links
- `aircbot what links do you have?` → Shows recent links  
- `bot search for python links` → Searches for "python"
- `bubba show me links by john` → Shows john's links
- `aircbot links stats please` → Shows statistics
- `bot show detailed links` → Shows links with timestamps

**Questions:**
- `bubba, what's the weather like?` → Asks LLM
- `aircbot explain quantum physics` → Asks LLM
- `bot, how does this work?` → Asks LLM

The bot responds to: `bubba`, `aircbot`, `bot` (case-insensitive, with word boundaries)

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

- `bot.py` - Main IRC bot logic with rate limiting
- `database.py` - Database operations
- `link_handler.py` - URL detection and metadata fetching  
- `llm_handler.py` - LLM integration for questions
- `rate_limiter.py` - Rate limiting functionality
- `config.py` - Configuration management
- `test_suite.py` - Comprehensive test suite

### Testing

Run the comprehensive test suite:
```bash
python test_suite.py              # Run all tests
python test_suite.py --test mentions  # Test mention detection
python test_suite.py --test links     # Test link request detection  
python test_suite.py --test rate      # Test rate limiting
python test_suite.py --test bot       # Test bot integration
python test_suite.py --test llm       # Test LLM validation
python test_suite.py --test flow      # Test complete flow
```

## Example Usage

### Automatic Link Saving
```
<user> Check out this cool project: https://github.com/example/repo
<aircbot> 📎 Saved: Example Repository - A cool project
```

### Traditional Commands  
```
<user> !links
<aircbot> 📚 Recent links:
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> !links search github
<aircbot> 🔍 Search results for 'github':
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> !ask what is python?
<aircbot> 🤖 Python is a high-level programming language known for its simplicity and readability.

<user> !ratelimit
<aircbot> ⏱️ Rate Limit Status:
<aircbot> • Total requests this minute: 3/10
<aircbot> • Active users: 2
<aircbot> • user: 1/1 (remaining: 0)
```

### Natural Language Mentions
```
<user> bubba, what links do you have?
<aircbot> 📚 Recent links:
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> aircbot search for python links
<aircbot> 🔍 Search results for 'python':
<aircbot> • Python Tutorial (by alice) - https://python.org/tutorial

<user> bot, explain machine learning
<aircbot> 🤖 Machine learning is a subset of AI that enables computers to learn from data.

<user> bubba tell me a joke
<aircbot> ⏱️ user: Please wait a moment before mentioning me again.
```

### Rate Limiting
The bot enforces rate limits to prevent spam:
- Each user is limited to a configurable number of requests per minute
- There's also a total limit across all users per minute  
- Users who exceed limits see friendly rate limit messages
- Rate limits reset automatically after the time window

## Requirements

- Python 3.7+
- Internet connection for fetching link metadata
- Access to IRC server
