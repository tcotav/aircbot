#!/usr/bin/env python3
"""
AircBot - IRC Bot with Link Memory
A simple IRC bot that captures and saves links shared in channels.
"""

import irc.bot
import irc.strings
import logging
import sys
from threading import Thread
import time

from config import Config
from database import Database
from link_handler import LinkHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AircBot(irc.bot.SingleServerIRCBot):
    def __init__(self):
        # Initialize components
        self.config = Config()
        self.db = Database(self.config.DATABASE_PATH)
        self.link_handler = LinkHandler()
        
        # IRC connection setup
        server = [(self.config.IRC_SERVER, self.config.IRC_PORT)]
        
        super().__init__(server, self.config.IRC_NICKNAME, self.config.IRC_NICKNAME)
        
        logger.info(f"Bot initialized for {self.config.IRC_SERVER}:{self.config.IRC_PORT}")
        logger.info(f"Will join channel: {self.config.IRC_CHANNEL}")
    
    def on_welcome(self, connection, event):
        """Called when we successfully connect to the IRC server"""
        logger.info("Connected to IRC server")
        
        # Join the configured channel
        connection.join(self.config.IRC_CHANNEL)
        logger.info(f"Joining channel {self.config.IRC_CHANNEL}")
    
    def on_join(self, connection, event):
        """Called when someone joins a channel"""
        channel = event.target
        nick = event.source.nick
        
        if nick == self.config.IRC_NICKNAME:
            logger.info(f"Successfully joined {channel}")
            # Send a greeting message
            connection.privmsg(channel, "🤖 AircBot is online! I'll save any links you share here.")
    
    def on_pubmsg(self, connection, event):
        """Called when a public message is received in a channel"""
        channel = event.target
        message = event.arguments[0]
        user = event.source.nick
        
        logger.info(f"[{channel}] <{user}> {message}")
        
        # Save message to database for context
        self.db.save_message(user, channel, message)
        
        # Check for commands
        if message.startswith(self.config.COMMAND_PREFIX):
            self.handle_command(connection, channel, user, message)
        
        # Extract and process links
        self.process_links(connection, channel, user, message)
    
    def handle_command(self, connection, channel, user, message):
        """Handle bot commands"""
        parts = message[1:].split()  # Remove prefix and split
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command == 'links':
            if not args:
                # Show recent links
                self.show_recent_links(connection, channel)
            elif args[0] == 'search' and len(args) > 1:
                # Search links
                query = ' '.join(args[1:])
                self.search_links(connection, channel, query)
            elif args[0] == 'stats':
                # Show statistics
                self.show_stats(connection, channel)
        
        elif command == 'help':
            self.show_help(connection, channel)
    
    def process_links(self, connection, channel, user, message):
        """Extract and save links from messages"""
        urls = self.link_handler.extract_urls(message)
        
        for url in urls:
            # Process link in a separate thread to avoid blocking
            thread = Thread(target=self._process_single_link, 
                          args=(connection, channel, user, url))
            thread.daemon = True
            thread.start()
    
    def _process_single_link(self, connection, channel, user, url):
        """Process a single link (runs in separate thread)"""
        try:
            logger.info(f"Processing link: {url}")
            
            # Get metadata
            title, description = self.link_handler.get_link_metadata(url)
            
            # Save to database
            saved = self.db.save_link(url, title, description, user, channel)
            
            if saved:
                # Announce the saved link
                response = f"📎 Saved: {title}"
                if len(response) > 300:  # IRC message length limit
                    response = response[:297] + "..."
                connection.privmsg(channel, response)
                logger.info(f"Saved link: {url} - {title}")
            else:
                logger.info(f"Link already exists: {url}")
                
        except Exception as e:
            logger.error(f"Error processing link {url}: {e}")
    
    def show_recent_links(self, connection, channel):
        """Show recent links in the channel"""
        links = self.db.get_recent_links(channel, limit=5)
        
        if not links:
            connection.privmsg(channel, "No links saved yet!")
            return
        
        connection.privmsg(channel, "📚 Recent links:")
        for link in links:
            msg = f"• {link['title']} (by {link['user']}) - {link['url']}"
            if len(msg) > 400:
                msg = msg[:397] + "..."
            connection.privmsg(channel, msg)
    
    def search_links(self, connection, channel, query):
        """Search for links matching a query"""
        links = self.db.search_links(channel, query, limit=3)
        
        if not links:
            connection.privmsg(channel, f"No links found matching '{query}'")
            return
        
        connection.privmsg(channel, f"🔍 Search results for '{query}':")
        for link in links:
            msg = f"• {link['title']} (by {link['user']}) - {link['url']}"
            if len(msg) > 400:
                msg = msg[:397] + "..."
            connection.privmsg(channel, msg)
    
    def show_stats(self, connection, channel):
        """Show link statistics"""
        stats = self.db.get_link_stats(channel)
        
        msg = f"📊 Stats: {stats.get('total_links', 0)} links saved by {stats.get('unique_users', 0)} users"
        if 'top_contributor' in stats:
            msg += f" (top: {stats['top_contributor']} with {stats['top_contributor_count']} links)"
        
        connection.privmsg(channel, msg)
    
    def show_help(self, connection, channel):
        """Show help information"""
        help_text = [
            "🤖 AircBot Commands:",
            "!links - Show recent links",
            "!links search <term> - Search saved links",
            "!links stats - Show statistics",
            "!help - Show this help",
            "I automatically save any links you share!"
        ]
        
        for line in help_text:
            connection.privmsg(channel, line)
    
    def on_disconnect(self, connection, event):
        """Called when disconnected from server"""
        logger.warning("Disconnected from IRC server")
    
    def on_error(self, connection, event):
        """Called when an error occurs"""
        logger.error(f"IRC Error: {event}")

def main():
    """Main entry point"""
    try:
        bot = AircBot()
        logger.info("Starting bot...")
        bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
