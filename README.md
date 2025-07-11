# AircBot

An intelligent IRC/Discord bot that automatically saves shared links and provides natural language interaction through LLM integration. Features smart link management, conversational AI responses, and comprehensive performance monitoring.

## Features

- **Multi-Platform**: Works on both IRC and Discord
- **Smart Link Management**: Automatically detects, saves, and organizes shared links with metadata
- **AI-Powered Conversations**: Natural language responses using local LLM with intelligent fallback to OpenAI
- **Privacy Protection**: Advanced filtering that anonymizes usernames and removes PII before sending to LLMs
- **Flexible Configuration**: Multiple LLM modes (local-only, OpenAI-only, or smart fallback)
- **Performance Optimized**: Built-in caching, rate limiting, and monitoring

## Quick Start

### IRC Bot
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
   ./run_tests.sh                # Run complete consolidated test suite (recommended)
   python -m pytest tests/test_consolidated.py -v  # Run tests with verbose output
   python demo.py                # Run interactive demo of privacy & admin features
   ```

4. **Run the bot:**
   ```bash
   ./start.sh  # Or: source venv/bin/activate && python bot.py
   ```

### Discord Bot
1. **Set up Discord application:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and bot
   - Copy the bot token
   - Enable "Message Content Intent" in Bot settings

2. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure the bot:**
   ```bash
   # Add to your .env file:
   DISCORD_TOKEN=your_bot_token_here
   ```

4. **Invite bot to server:**
   - Generate an invite link with these permissions:
     - Send Messages
     - Read Message History
     - Use Slash Commands (optional)
   - Invite the bot to your Discord server

5. **Run the Discord bot:**
   ```bash
   ./start_discord.sh  # Or: source venv/bin/activate && python simple_discord_bot.py
   ```

## Privacy Protection

AircBot includes an advanced privacy filter to protect user information when sending conversation context to LLMs. The privacy filter:

- **Anonymizes usernames** while preserving conversation flow
- **Removes PII** including emails, phone numbers, IPs, SSNs, and credit cards
- **Handles mentions and addressing** (e.g., "@john" becomes "@user_1")
- **Preserves common words** to avoid breaking normal conversation
- **Optimizes for channel size** with configurable performance thresholds
- **Maintains conversation context** so LLMs can still provide relevant responses

The privacy filter is enabled by default and works transparently. For complete documentation, configuration options, and examples, see the **[Privacy Filter Guide](docs/PRIVACY_FILTER_GUIDE.md)**.

## Configuration

Copy `.env.example` to `.env` and customize your settings:

```bash
cp .env.example .env
# Edit .env with your IRC/Discord server details and preferences
```

### Quick Configuration Examples

**Local AI Only** (free, private):
```bash
LLM_MODE=local_only
LLM_ENABLED=true
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=deepseek-r1:latest
```

**OpenAI Only** (reliable, paid):
```bash
LLM_MODE=openai_only
OPENAI_ENABLED=true
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Smart Fallback** (best of both worlds):
```bash
LLM_MODE=fallback
LLM_ENABLED=true
OPENAI_ENABLED=true
SEMANTIC_SIMILARITY_ENABLED=true  # AI-powered response quality detection
```

📖 **For complete configuration options, see [Configuration Guide](docs/CONFIGURATION.md)**

## Commands

Both IRC and Discord versions support the same command set:

### Traditional Commands
- `!links` - Show recent links
- `!links search <term>` - Search saved links by keyword
- `!links by <user>` - Show links shared by specific user (IRC only)
- `!links stats` - Show link statistics 
- `!links details` - Show recent links with timestamps (IRC only)
- `!ask <question>` - Ask the LLM a question
- `!privacy` - Show privacy filter status
- `!privacy test <message>` - Test privacy filter on a message
- `!privacy clear` - Clear your anonymization mappings (admin only)
- `!ratelimit` - Show rate limit status (IRC only)
- `!performance` - Show LLM performance stats (IRC only)
- `!bothelp` - Show help information (Discord) / `!help` (IRC)

### Natural Language

**IRC (Bot Mentions):**
You can mention the bot by name and ask naturally:
- `<ircnick>, show me the links` → Shows recent links
- `aircbot what links do you have?` → Shows recent links  

**Discord (Direct Mentions):**
Use @mentions or direct messages:
- `@aircbot show me the links` → Shows recent links
- `@aircbot what's the weather like?` → Asks LLM
- Direct message the bot for private conversations

The IRC bot responds to: ircnick, `aircbot` (case-insensitive, with word boundaries)

## Database Schema

The bot creates these tables:

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

### user_mappings (privacy)
- `real_username` - Original username
- `anonymous_id` - Anonymized identifier
- `channel` - Channel context
- `created_at` - Mapping creation time

### channel_users (privacy)
- `channel` - Channel name
- `username` - User in channel
- `last_seen` - Last activity timestamp

## Architecture

AircBot is built with a modular architecture:

### Core Components
- **Bot Platforms**: `bot.py` (IRC), `simple_discord_bot.py` (Discord)
- **AI Integration**: `llm_handler.py` with smart fallback logic and semantic similarity
- **Link Management**: `link_handler.py` for URL detection and metadata
- **Privacy Protection**: `privacy_filter.py` with PII detection and anonymization
- **Database**: `database.py` with SQLite for persistence
- **Configuration**: `config.py` with comprehensive validation

### Key Features
- **Smart Fallback**: Tries local AI first, falls back to OpenAI if response quality is poor
- **Semantic Similarity**: AI-powered response quality evaluation beyond keyword matching
- **Privacy First**: Automatic PII filtering and username anonymization
- **Performance Optimized**: Built-in caching, rate limiting, and monitoring

## Development

### Testing

Run the comprehensive test suite to validate functionality:

```bash
# Run complete test suite (recommended)
./run_tests.sh

# Run specific test categories
python tests/test_fallback_logic.py        # Fallback logic tests
python tests/test_semantic_similarity.py   # Semantic similarity tests
python tests/test_privacy_filter.py       # Privacy filter tests
python demo.py                            # Interactive demonstration
```

### Contributing

The codebase follows a clean, modular architecture:
- Each component has a single responsibility
- Comprehensive test coverage for all features
- Clear separation between IRC/Discord platforms and core logic
- Well-documented configuration options

## Example Usage

### Automatic Link Saving (Both Platforms)
**IRC:**
```
<user> Check out this cool project: https://github.com/example/repo
<aircbot> 📎 Saved: Example Repository - A cool project
```

**Discord:**
```
user: Check out this cool project: https://github.com/example/repo
aircbot: 📎 Saved: Example Repository - A cool project
```

### Traditional Commands
**IRC:**
```
<user> !links
<aircbot> 📚 Recent links:
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> !links search github
<aircbot> 🔍 Search results for 'github':
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> !ask what is python?
<aircbot> 🤖 Python is a high-level programming language known for its simplicity and readability.
```

**Discord:**
```
user: !bothelp
aircbot: 🤖 **AircBot Discord Commands**

**Link Management:**
• !links - Show recent links
• !links search <term> - Search for links
• !links stats - Show link statistics

user: !ask what is python?
aircbot: 🤖 Python is a high-level programming language known for its simplicity and readability.
```

### Natural Language Mentions
**IRC:**
```
<user> bubba, what links do you have?
<aircbot> 📚 Recent links:
<aircbot> • Example Repository (by user) - https://github.com/example/repo

<user> bot, explain machine learning
<aircbot> 🤖 Machine learning is a subset of AI that enables computers to learn from data.
```

**Discord:**
```
user: @aircbot what links do you have?
aircbot: 📚 Recent links:
• Example Repository (by user) - https://github.com/example/repo

user: @aircbot explain machine learning
aircbot: 🤖 Machine learning is a subset of AI that enables computers to learn from data.
```

### Privacy Protection
The privacy filter automatically protects user information:

**IRC:**
```
<john_doe> Check out my email john.doe@company.com for updates
<alice_smith> @john_doe sounds good, I'll email you at alice@example.org

<user> !ask What did john say about email?
<aircbot> 🤖 user_1 mentioned sharing an email address for updates. user_2 said they would send an email as well.
```

**Discord:**
```
user: !privacy test Contact me at (555) 123-4567 or my GitHub @john_doe
aircbot: 🔒 **Privacy Filter Test:**
**Original:** Contact me at (555) 123-4567 or my GitHub @john_doe
**Filtered:** Contact me at [PHONE_REDACTED] or my GitHub @user_1

user: !privacy
aircbot: 🔒 **Privacy Filter Status:**
✅ Privacy filtering: **ENABLED**
📊 Channel size: 12 users (threshold: 50)
🔄 Full filtering mode active
📝 Anonymized users: 5
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
- For IRC: Access to IRC server
- For Discord: Discord bot token and server permissions

### Platform-Specific Requirements

**IRC:**
- Access to IRC server (default: irc.libera.chat)
- Optional: SSL support for secure connections

**Discord:**
- Discord application and bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- Bot permissions: Send Messages, Read Message History
- Message Content Intent enabled in Discord Developer Portal
