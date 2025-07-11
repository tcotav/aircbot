# AircBot Configuration Guide

This guide covers all configuration options for AircBot. Copy `.env.example` to `.env` and modify as needed.

## Quick Setup

```bash
cp .env.example .env
# Edit .env with your settings
```

## Core Configuration

### IRC Settings
- `IRC_SERVER` - IRC server address (default: irc.libera.chat)
- `IRC_PORT` - IRC server port (default: 6667)  
- `IRC_NICKNAME` - Bot's nickname
- `IRC_CHANNEL` - Channel to join (include # prefix)
- `IRC_PASSWORD` - Bot's password (if required)
- `IRC_USE_SSL` - Enable SSL connection (true/false)
- `IRC_SSL_VERIFY` - Verify SSL certificates (false for self-signed)

### Discord Settings
- `DISCORD_TOKEN` - Your Discord bot token (required for Discord bot)
- `DISCORD_GUILD_ID` - Optional: Specific server ID to restrict bot to
- `DISCORD_CHANNEL_ID` - Optional: Specific channel ID to restrict bot to

## LLM Configuration

### LLM Mode Selection
Configure which AI service to use:

```bash
# Use only local AI (Ollama) - Free, private, fast
LLM_MODE=local_only

# Use only OpenAI API - Reliable, costs money
LLM_MODE=openai_only

# Try local first, fallback to OpenAI if needed - Best of both worlds
LLM_MODE=fallback
```

### Local LLM Settings (Ollama)
- `LLM_ENABLED` - Enable local LLM features (true/false)
- `LLM_BASE_URL` - API endpoint (e.g., http://localhost:11434/v1 for Ollama)
- `LLM_API_KEY` - API key (use "ollama" for local Ollama)
- `LLM_MODEL` - Model name (e.g., deepseek-r1:latest)
- `LLM_MAX_TOKENS` - Maximum response length (default: 150)
- `LLM_TEMPERATURE` - Creativity level 0.0-1.0 (default: 0.7)
- `LLM_RETRY_ATTEMPTS` - Number of retries for empty LLM responses (default: 3)

### OpenAI Settings

**🔐 IMPORTANT: Set your OpenAI API key in your environment for security:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

- `OPENAI_ENABLED` - Enable OpenAI API features (auto-enabled when API key is found)
- `OPENAI_MODEL` - OpenAI model to use (e.g., gpt-3.5-turbo, gpt-4)
- `OPENAI_MAX_TOKENS` - Maximum response length for OpenAI (default: 150)
- `OPENAI_TEMPERATURE` - Creativity level for OpenAI 0.0-1.0 (default: 0.7)
- `OPENAI_DAILY_LIMIT` - Maximum OpenAI API calls per day for cost control (default: 100)

## Advanced Features

### Fallback Mode with Semantic Similarity

When using `LLM_MODE=fallback`, the bot can use advanced AI-powered response quality evaluation:

```bash
# Enable intelligent fallback decisions (requires: pip install sentence-transformers)
SEMANTIC_SIMILARITY_ENABLED=true
SEMANTIC_SIMILARITY_MIN_THRESHOLD=0.3
```

The bot will:
1. Try local AI first (faster, free, private)
2. If local AI gives a poor response, automatically fall back to OpenAI
3. Use semantic similarity to detect when responses miss the point, not just keyword matching

For complete fallback configuration options, see **[Fallback Configuration Guide](FALLBACK_CONFIGURATION.md)**.

### Personality Prompts

Customize the bot's personality and response style:

```bash
# Enable personality prompts
PERSONALITY_ENABLED=true
PERSONALITY_PROMPT_FILE=personality_prompt.txt

# Create personality file
echo "Respond in a helpful but concise manner." > personality_prompt.txt
```

### Privacy Protection

The bot includes advanced privacy filtering:

```bash
# Privacy settings
PRIVACY_FILTER_ENABLED=true
PRIVACY_LEVEL=medium  # none, low, medium, high, paranoid
PRIVACY_USERNAME_ANONYMIZATION=true
PRIVACY_PII_DETECTION=true
```

For complete privacy configuration, see **[Privacy Filter Guide](PRIVACY_FILTER_GUIDE.md)**.

## Database and Performance

### Database
- `DATABASE_PATH` - Path to SQLite database file (default: data/links.db)

### Rate Limiting  
- `RATE_LIMIT_USER_PER_MINUTE` - Max requests per user per minute (default: 1)
- `RATE_LIMIT_TOTAL_PER_MINUTE` - Max total requests per minute (default: 10)

### Link Display Limits
- `LINKS_RECENT_LIMIT` - Number of links shown by `!links` command (default: 5)
- `LINKS_SEARCH_LIMIT` - Number of links shown by `!links search` command (default: 3)
- `LINKS_DETAILS_LIMIT` - Number of links shown by `!links details` command (default: 5)
- `LINKS_BY_USER_LIMIT` - Number of links shown by `!links by <user>` command (default: 3)

### Administrative Settings
- `ADMIN_USERS` - Comma-separated list of admin usernames (default: bot nickname)

## Configuration Examples

### Local-Only Setup (Free, Private)
```bash
LLM_MODE=local_only
LLM_ENABLED=true
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=deepseek-r1:latest
OPENAI_ENABLED=false
SEMANTIC_SIMILARITY_ENABLED=false
```

### OpenAI-Only Setup (Reliable, Costs Money)
```bash
LLM_MODE=openai_only
LLM_ENABLED=false
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_DAILY_LIMIT=100
SEMANTIC_SIMILARITY_ENABLED=false
```

### Fallback Setup (Best of Both Worlds)
```bash
LLM_MODE=fallback
LLM_ENABLED=true
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=deepseek-r1:latest
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-3.5-turbo
SEMANTIC_SIMILARITY_ENABLED=true
SEMANTIC_SIMILARITY_MIN_THRESHOLD=0.3
```

## Related Documentation

- **[Fallback Configuration Guide](FALLBACK_CONFIGURATION.md)** - Complete fallback system configuration
- **[Privacy Filter Guide](PRIVACY_FILTER_GUIDE.md)** - Privacy protection settings
- **[Performance and Monitoring](PERFORMANCE_LOGGING.md)** - Performance tuning and monitoring

## Getting Help

For configuration questions:
1. Check the relevant documentation guides linked above
2. Review the `.env.example` file for all available options
3. Run the test suite to validate your configuration
4. Check the logs for configuration errors on startup