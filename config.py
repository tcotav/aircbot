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
    
    # Discord Settings
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
    DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID', '')  # Optional: specific server ID
    DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID', '')  # Optional: specific channel ID
    
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
    
    # OpenAI Settings
    # Use environment OPENAI_API_KEY directly (preferred for security)
    # Fall back to OPENAI_API_KEY env var set by user, then config value
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY_CONFIG', '')
    OPENAI_ENABLED = os.getenv('OPENAI_ENABLED', 'true' if OPENAI_API_KEY else 'false').lower() == 'true'
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    OPENAI_DAILY_LIMIT = int(os.getenv('OPENAI_DAILY_LIMIT', '100'))  # Max OpenAI calls per day
    
    # LLM Mode Settings
    # Modes: 'local_only', 'openai_only', 'fallback' (try local first, then OpenAI)
    LLM_MODE = os.getenv('LLM_MODE', 'local_only')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/links.db')
    
    # Rate Limiting
    RATE_LIMIT_USER_PER_MINUTE = int(os.getenv('RATE_LIMIT_USER_PER_MINUTE', '1'))
    RATE_LIMIT_TOTAL_PER_MINUTE = int(os.getenv('RATE_LIMIT_TOTAL_PER_MINUTE', '10'))
    
    # Bot behavior
    COMMAND_PREFIX = '!'
    
    # Link display limits
    LINKS_RECENT_LIMIT = int(os.getenv('LINKS_RECENT_LIMIT', '5'))  # Default: 5 links for !links
    LINKS_SEARCH_LIMIT = int(os.getenv('LINKS_SEARCH_LIMIT', '3'))  # Default: 3 links for !links search
    LINKS_DETAILS_LIMIT = int(os.getenv('LINKS_DETAILS_LIMIT', '5'))  # Default: 5 links for !links details
    LINKS_BY_USER_LIMIT = int(os.getenv('LINKS_BY_USER_LIMIT', '3'))  # Default: 3 links for !links by user
    
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

    # Content Filter Settings
    CONTENT_FILTER_ENABLED = os.getenv('CONTENT_FILTER_ENABLED', 'true').lower() == 'true'
    CONTENT_FILTER_LLM_ASSIST = os.getenv('CONTENT_FILTER_LLM_ASSIST', 'true').lower() == 'true'
    CONTENT_FILTER_LOG_BLOCKED = os.getenv('CONTENT_FILTER_LOG_BLOCKED', 'true').lower() == 'true'
    CONTENT_FILTER_MAX_MESSAGE_LENGTH = int(os.getenv('CONTENT_FILTER_MAX_MESSAGE_LENGTH', '1000'))
    CONTENT_FILTER_STRICT_MODE = os.getenv('CONTENT_FILTER_STRICT_MODE', 'false').lower() == 'true'
    CONTENT_FILTER_BLOCK_PII = os.getenv('CONTENT_FILTER_BLOCK_PII', 'true').lower() == 'true'
    CONTENT_FILTER_BLOCK_EXCESSIVE_CAPS = os.getenv('CONTENT_FILTER_BLOCK_EXCESSIVE_CAPS', 'true').lower() == 'true'

    # Privacy Filter Settings
    PRIVACY_FILTER_ENABLED = os.getenv('PRIVACY_FILTER_ENABLED', 'true').lower() == 'true'
    PRIVACY_LEVEL = os.getenv('PRIVACY_LEVEL', 'medium')  # none, low, medium, high, paranoid
    PRIVACY_MAX_CHANNEL_USERS = int(os.getenv('PRIVACY_MAX_CHANNEL_USERS', '20'))  # Skip privacy for large channels
    PRIVACY_USERNAME_ANONYMIZATION = os.getenv('PRIVACY_USERNAME_ANONYMIZATION', 'true').lower() == 'true'
    PRIVACY_PII_DETECTION = os.getenv('PRIVACY_PII_DETECTION', 'true').lower() == 'true'
    PRIVACY_PRESERVE_CONVERSATION_FLOW = os.getenv('PRIVACY_PRESERVE_CONVERSATION_FLOW', 'true').lower() == 'true'

    # Personality Prompt Settings
    # Enable custom personality prompts for the bot
    PERSONALITY_ENABLED = os.getenv('PERSONALITY_ENABLED', 'false').lower() == 'true'
    # Path to personality prompt file
    PERSONALITY_PROMPT_FILE = os.getenv('PERSONALITY_PROMPT_FILE', 'personality_prompt.txt')
    
    # LLM Fallback Configuration
    # These settings control when the bot falls back from local LLM to OpenAI
    
    # Minimum response length before considering fallback (characters)
    FALLBACK_MIN_RESPONSE_LENGTH = int(os.getenv('FALLBACK_MIN_RESPONSE_LENGTH', '3'))
    
    # Minimum response length for "I don't know" context check (words)
    FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS = int(os.getenv('FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS', '15'))
    
    # Relevance scoring thresholds
    FALLBACK_RELEVANCE_MIN_RATIO = float(os.getenv('FALLBACK_RELEVANCE_MIN_RATIO', '0.05'))
    FALLBACK_RELEVANCE_MIN_QUESTION_WORDS = int(os.getenv('FALLBACK_RELEVANCE_MIN_QUESTION_WORDS', '3'))
    
    # Question type mismatch thresholds
    FALLBACK_TYPE_MISMATCH_MIN_RATIO = float(os.getenv('FALLBACK_TYPE_MISMATCH_MIN_RATIO', '0.1'))
    FALLBACK_TYPE_MISMATCH_MIN_QUESTION_WORDS = int(os.getenv('FALLBACK_TYPE_MISMATCH_MIN_QUESTION_WORDS', '5'))
    
    # Generic response detection threshold (words)
    FALLBACK_GENERIC_RESPONSE_MAX_WORDS = int(os.getenv('FALLBACK_GENERIC_RESPONSE_MAX_WORDS', '25'))
    
    # Repetition detection thresholds
    FALLBACK_REPETITION_MAX_WORD_RATIO = float(os.getenv('FALLBACK_REPETITION_MAX_WORD_RATIO', '0.3'))
    FALLBACK_REPETITION_MIN_WORD_LENGTH = int(os.getenv('FALLBACK_REPETITION_MIN_WORD_LENGTH', '3'))
    
    # Explanation response minimum word count
    FALLBACK_EXPLANATION_MIN_WORDS = int(os.getenv('FALLBACK_EXPLANATION_MIN_WORDS', '8'))
    
    # Procedural response minimum word count for short answer bypass
    FALLBACK_PROCEDURAL_SHORT_ANSWER_MAX_WORDS = int(os.getenv('FALLBACK_PROCEDURAL_SHORT_ANSWER_MAX_WORDS', '15'))
    
    # Code response minimum word count for short answer bypass
    FALLBACK_CODE_SHORT_ANSWER_MAX_WORDS = int(os.getenv('FALLBACK_CODE_SHORT_ANSWER_MAX_WORDS', '10'))
    
    # Semantic Similarity Configuration
    # Enable semantic similarity scoring for fallback decisions
    SEMANTIC_SIMILARITY_ENABLED = os.getenv('SEMANTIC_SIMILARITY_ENABLED', 'false').lower() == 'true'
    
    # Semantic similarity thresholds
    SEMANTIC_SIMILARITY_MIN_THRESHOLD = float(os.getenv('SEMANTIC_SIMILARITY_MIN_THRESHOLD', '0.3'))
    SEMANTIC_SIMILARITY_WEIGHT = float(os.getenv('SEMANTIC_SIMILARITY_WEIGHT', '0.4'))  # Weight in combined scoring
    
    # Model configuration for semantic similarity
    SEMANTIC_MODEL_NAME = os.getenv('SEMANTIC_MODEL_NAME', 'all-MiniLM-L6-v2')  # Lightweight model
    SEMANTIC_MODEL_DEVICE = os.getenv('SEMANTIC_MODEL_DEVICE', 'cpu')  # 'cpu' or 'cuda'
    SEMANTIC_CACHE_SIZE = int(os.getenv('SEMANTIC_CACHE_SIZE', '100'))  # Cache embeddings
    
    # Context-aware semantic scoring
    SEMANTIC_CONTEXT_ENABLED = os.getenv('SEMANTIC_CONTEXT_ENABLED', 'true').lower() == 'true'
    SEMANTIC_CONTEXT_WEIGHT = float(os.getenv('SEMANTIC_CONTEXT_WEIGHT', '0.2'))  # Weight for context matching
    
    # Entity/keyword boosting
    SEMANTIC_ENTITY_BOOST = float(os.getenv('SEMANTIC_ENTITY_BOOST', '1.2'))  # Boost for technical terms
    SEMANTIC_TECHNICAL_KEYWORDS = [kw.strip() for kw in os.getenv('SEMANTIC_TECHNICAL_KEYWORDS', 'code,function,class,api,database,server,config,install,debug,error,fix,implement,create,build,deploy,test,python,javascript,sql,git,docker,linux,windows,network,security,performance').split(',')]
    
    # Validate semantic similarity configuration
    if SEMANTIC_SIMILARITY_ENABLED:
        if not (0.0 <= SEMANTIC_SIMILARITY_MIN_THRESHOLD <= 1.0):
            raise ValueError(f"SEMANTIC_SIMILARITY_MIN_THRESHOLD must be between 0.0 and 1.0, got {SEMANTIC_SIMILARITY_MIN_THRESHOLD}")
        if not (0.0 <= SEMANTIC_SIMILARITY_WEIGHT <= 1.0):
            raise ValueError(f"SEMANTIC_SIMILARITY_WEIGHT must be between 0.0 and 1.0, got {SEMANTIC_SIMILARITY_WEIGHT}")
        if not (0.0 <= SEMANTIC_CONTEXT_WEIGHT <= 1.0):
            raise ValueError(f"SEMANTIC_CONTEXT_WEIGHT must be between 0.0 and 1.0, got {SEMANTIC_CONTEXT_WEIGHT}")
        if SEMANTIC_CACHE_SIZE < 0:
            raise ValueError(f"SEMANTIC_CACHE_SIZE must be non-negative, got {SEMANTIC_CACHE_SIZE}")
    
    # Validate personality configuration
    if PERSONALITY_ENABLED:
        if not os.path.exists(PERSONALITY_PROMPT_FILE):
            raise ValueError(
                f"Personality prompt misconfiguration: PERSONALITY_ENABLED=true but "
                f"PERSONALITY_PROMPT_FILE ('{PERSONALITY_PROMPT_FILE}') does not exist. "
                f"Please either:\n"
                f"1. Create the file '{PERSONALITY_PROMPT_FILE}' with your personality prompt, or\n"
                f"2. Set PERSONALITY_ENABLED=false to disable personality prompts"
            )
        
        # Check if file is empty
        with open(PERSONALITY_PROMPT_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise ValueError(
                    f"Personality prompt misconfiguration: PERSONALITY_ENABLED=true but "
                    f"PERSONALITY_PROMPT_FILE ('{PERSONALITY_PROMPT_FILE}') is empty. "
                    f"Please add your personality prompt to the file or set PERSONALITY_ENABLED=false"
                )

    # Admin Settings
    # Comma-separated list of admin usernames who can use admin commands
    ADMIN_USERS = [user.strip() for user in os.getenv('ADMIN_USERS', '').split(',') if user.strip()]
    # If no admins specified, the bot owner (IRC_NICKNAME) is automatically admin
    if not ADMIN_USERS and IRC_NICKNAME:
        ADMIN_USERS = [IRC_NICKNAME]
