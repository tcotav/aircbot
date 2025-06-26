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
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/links.db')
    
    # Bot behavior
    COMMAND_PREFIX = '!'
