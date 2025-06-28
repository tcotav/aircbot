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
    
    # Private messaging settings
    PRIVATE_MSG_ENABLED = os.getenv('PRIVATE_MSG_ENABLED', 'true').lower() == 'true'
    LINKS_USE_PRIVATE_MSG = os.getenv('LINKS_USE_PRIVATE_MSG', 'true').lower() == 'true'
    COMMANDS_USE_PRIVATE_MSG = os.getenv('COMMANDS_USE_PRIVATE_MSG', 'true').lower() == 'true'
    
    # Message Context Settings
    MESSAGE_QUEUE_SIZE = int(os.getenv('MESSAGE_QUEUE_SIZE', '50'))  # Local queue size per channel
    CONTEXT_ANALYSIS_ENABLED = os.getenv('CONTEXT_ANALYSIS_ENABLED', 'true').lower() == 'true'
    CONTEXT_RELEVANCE_THRESHOLD = float(os.getenv('CONTEXT_RELEVANCE_THRESHOLD', '0.3'))  # 0.0-1.0
    SAVE_MESSAGES_TO_DB = os.getenv('SAVE_MESSAGES_TO_DB', 'false').lower() == 'true'
    MAX_CONTEXT_MESSAGES = int(os.getenv('MAX_CONTEXT_MESSAGES', '10'))  # Max messages to include as context
    
    # Context Relevance Scoring Weights (should sum to reasonable total, e.g., ~1.0)
    WEIGHT_KEYWORD_OVERLAP = float(os.getenv('WEIGHT_KEYWORD_OVERLAP', '0.4'))  # Direct word matches
    WEIGHT_TECHNICAL_KEYWORDS = float(os.getenv('WEIGHT_TECHNICAL_KEYWORDS', '0.3'))  # Technical term bonus
    WEIGHT_QUESTION_CONTEXT = float(os.getenv('WEIGHT_QUESTION_CONTEXT', '0.15'))  # Question/answer bonus
    WEIGHT_RECENCY_BONUS = float(os.getenv('WEIGHT_RECENCY_BONUS', '0.1'))  # Recent message bonus
    WEIGHT_BOT_INTERACTION = float(os.getenv('WEIGHT_BOT_INTERACTION', '0.1'))  # Command/mention bonus
    WEIGHT_URL_BONUS = float(os.getenv('WEIGHT_URL_BONUS', '0.2'))  # URL/link bonus
    PENALTY_SHORT_MESSAGE = float(os.getenv('PENALTY_SHORT_MESSAGE', '0.7'))  # Multiplier for short messages
