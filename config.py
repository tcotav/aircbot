import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # IRC Settings
    IRC_SERVER = os.getenv('IRC_SERVER', 'irc.libera.chat')
    IRC_PORT = int(os.getenv('IRC_PORT', 6667))
    IRC_NICKNAME = os.getenv('IRC_NICKNAME', 'aircbot')
    IRC_CHANNEL = os.getenv('IRC_CHANNEL', '#test')
    IRC_PASSWORD = os.getenv('IRC_PASSWORD', '')
    IRC_SERVER_PASSWORD = os.getenv('IRC_SERVER_PASSWORD', '')
    
    # SSL Settings
    IRC_USE_SSL = os.getenv('IRC_USE_SSL', 'false').lower() == 'true'
    IRC_SSL_VERIFY = os.getenv('IRC_SSL_VERIFY', 'true').lower() == 'true'
    
    # LLM Settings (for Ollama with OpenAI-compatible API)
    LLM_ENABLED = os.getenv('LLM_ENABLED', 'false').lower() == 'true'
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1')
    LLM_API_KEY = os.getenv('LLM_API_KEY', 'ollama')  # Ollama doesn't need a real key
    LLM_MODEL = os.getenv('LLM_MODEL', 'llama3.2')
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '500'))
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    LLM_RETRY_ATTEMPTS = int(os.getenv('LLM_RETRY_ATTEMPTS', '3'))  # Retry on empty responses
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/links.db')
    
    # Rate Limiting
    RATE_LIMIT_USER_PER_MINUTE = int(os.getenv('RATE_LIMIT_USER_PER_MINUTE', '1'))
    RATE_LIMIT_TOTAL_PER_MINUTE = int(os.getenv('RATE_LIMIT_TOTAL_PER_MINUTE', '10'))
    
    # Bot behavior
    COMMAND_PREFIX = '!'
    
    # Message Context Settings
    MESSAGE_QUEUE_SIZE = int(os.getenv('MESSAGE_QUEUE_SIZE', '50'))  # Local queue size per channel
    CONTEXT_ANALYSIS_ENABLED = os.getenv('CONTEXT_ANALYSIS_ENABLED', 'true').lower() == 'true'
    CONTEXT_RELEVANCE_THRESHOLD = float(os.getenv('CONTEXT_RELEVANCE_THRESHOLD', '0.3'))  # 0.0-1.0
    SAVE_MESSAGES_TO_DB = os.getenv('SAVE_MESSAGES_TO_DB', 'false').lower() == 'true'
    MAX_CONTEXT_MESSAGES = int(os.getenv('MAX_CONTEXT_MESSAGES', '10'))  # Max messages to include as context
