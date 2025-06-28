#!/usr/bin/env python3
"""
AircBot - IRC Bot with Link Memory
A simple IRC bot that captures and saves links shared in channels.
"""

import irc.bot
import irc.strings
import irc.connection
import ssl
import logging
import sys
from threading import Thread
import time

from config import Config
from database import Database
from link_handler import LinkHandler
from llm_handler import LLMHandler
from rate_limiter import RateLimiter
from prompts import get_thinking_message
from context_manager import ContextManager

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
        self.llm_handler = LLMHandler(self.config)
        self.rate_limiter = RateLimiter(
            user_limit_per_minute=self.config.RATE_LIMIT_USER_PER_MINUTE,
            total_limit_per_minute=self.config.RATE_LIMIT_TOTAL_PER_MINUTE
        )
        self.context_manager = ContextManager(self.config)
        
        # Configure SSL context if needed
        ssl_factory = None
        if self.config.IRC_USE_SSL:
            ssl_context = ssl.create_default_context()
            if not self.config.IRC_SSL_VERIFY:
                # Allow self-signed certificates
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.warning("SSL certificate verification disabled - using self-signed certificates")
            ssl_factory = irc.connection.Factory(wrapper=ssl_context.wrap_socket)
        
        # IRC connection setup
        server = [(self.config.IRC_SERVER, self.config.IRC_PORT)]
        
        super().__init__(server, self.config.IRC_NICKNAME, self.config.IRC_NICKNAME, 
                         connect_factory=ssl_factory)
        
        logger.info(f"Bot initialized for {self.config.IRC_SERVER}:{self.config.IRC_PORT}")
        logger.info(f"SSL enabled: {self.config.IRC_USE_SSL}")
        logger.info(f"SSL verify: {self.config.IRC_SSL_VERIFY}")
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
            connection.privmsg(channel, "🤖 AircBot is online!")
    
    def on_pubmsg(self, connection, event):
        """Called when a public message is received in a channel"""
        channel = event.target
        message = event.arguments[0]
        user = event.source.nick
        
        # Determine message type for context
        is_command = message.startswith(self.config.COMMAND_PREFIX)
        is_bot_mention = self.is_bot_mentioned(message)
        
        # Add message to local context queue
        self.context_manager.add_message(user, channel, message, is_command, is_bot_mention)
        
        # Save message to database if enabled
        if self.config.SAVE_MESSAGES_TO_DB:
            self.db.save_message(user, channel, message)
        
        # Check for commands
        if is_command:
            self.handle_command(connection, channel, user, message)
        # Check if bot is mentioned by name
        elif is_bot_mention:
            self.handle_name_mention(connection, channel, user, message)
        
        # Extract and process links
        self.process_links(connection, channel, user, message)
    
    def on_privmsg(self, connection, event):
        """Called when a private message is received"""
        user = event.source.nick
        message = event.arguments[0]
        
        if not self.config.PRIVATE_MSG_ENABLED:
            connection.privmsg(user, "Private messaging is disabled. Please use commands in the channel.")
            return
        
        logger.info(f"Private message from {user}: {message}")
        
        # Check rate limit for private messages too
        if not self.rate_limiter.is_allowed(user):
            logger.info(f"Rate limited private message from {user}: {message}")
            connection.privmsg(user, "⏱️ Please wait a moment before sending another message.")
            return
        
        # Handle commands in private messages
        if message.startswith(self.config.COMMAND_PREFIX):
            # For private commands, pass user as "channel" so responses go back to user
            self.handle_command(connection, user, user, message, is_private=True)
        else:
            # Regular conversation - treat as an ask command
            if self.llm_handler.is_enabled():
                thinking_msg = f"🤖 Thinking about your message..."
                connection.privmsg(user, thinking_msg)
                
                # Process in a separate thread
                thread = Thread(target=self._process_private_conversation, 
                              args=(connection, user, message))
                thread.daemon = True
                thread.start()
            else:
                connection.privmsg(user, "Hi! I can help with link management. Try sending me commands like '!links' or '!help'.")
    
    def _process_private_conversation(self, connection, user, message):
        """Process private conversation using LLM"""
        try:
            # For private conversations, we could use a different context approach
            # For now, let's use a simple conversation without channel context
            response = self.llm_handler.ask_llm(message, "")
            
            if response:
                cleaned_response = self._clean_response_for_irc(response)
                self._send_long_message(connection, user, f"🤖 {cleaned_response}")
                logger.info(f"Responded to private conversation with {user}")
            else:
                connection.privmsg(user, "❌ Sorry, I couldn't process your message right now.")
                
        except Exception as e:
            logger.error(f"Error in private conversation with {user}: {e}")
            connection.privmsg(user, "❌ Something went wrong. Please try again later.")
    
    def handle_command(self, connection, channel, user, message, is_private=False):
        """Handle bot commands with rate limiting"""
        # Check rate limit
        if not self.rate_limiter.is_allowed(user):
            logger.info(f"Rate limited command from {user}: {message}")
            connection.privmsg(channel, f"⏱️ {user}: Please wait a moment before sending another command.")
            return
        
        parts = message[1:].split()  # Remove prefix and split
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command == 'links':
            # Determine if we should use private messaging
            use_private = self._should_use_private_message(is_private)
            target_channel = channel if not use_private else user
            
            if not args:
                # Show recent links
                self.show_recent_links(connection, target_channel, user if use_private else None)
            elif args[0] == 'search' and len(args) > 1:
                # Search links
                query = ' '.join(args[1:])
                self.search_links(connection, target_channel, query, user if use_private else None)
            elif args[0] == 'stats':
                # Show statistics
                self.show_stats(connection, target_channel, user if use_private else None)
            elif args[0] == 'details':
                # Show detailed link information
                self.show_detailed_links(connection, target_channel, user if use_private else None)
            elif args[0] == 'by' and len(args) > 1:
                # Show links by specific user
                username = args[1]
                self.show_links_by_user(connection, target_channel, username, user if use_private else None)
            
            # If we sent a private message, announce in channel
            if use_private:
                connection.privmsg(channel, f"📩 Sent link information to {user} via private message.")
        
        elif command == 'help':
            # Determine if we should use private messaging
            use_private = self.config.COMMANDS_USE_PRIVATE_MSG and not is_private
            target_channel = channel if not use_private else user
            self.show_help(connection, target_channel)
            if use_private:
                connection.privmsg(channel, f"📩 Sent help information to {user} via private message.")
        
        elif command == 'ratelimit' or command == 'rl':
            # Determine if we should use private messaging
            use_private = self.config.COMMANDS_USE_PRIVATE_MSG and not is_private
            target_channel = channel if not use_private else user
            self.show_rate_limit_stats(connection, target_channel, user)
            if use_private:
                connection.privmsg(channel, f"📩 Sent rate limit info to {user} via private message.")
        
        elif command == 'performance' or command == 'perf':
            # Determine if we should use private messaging
            use_private = self.config.COMMANDS_USE_PRIVATE_MSG and not is_private
            target_channel = channel if not use_private else user
            self.show_performance_stats(connection, target_channel)
            if use_private:
                connection.privmsg(channel, f"📩 Sent performance stats to {user} via private message.")
        
        elif command == 'context':
            # Determine if we should use private messaging
            use_private = self.config.COMMANDS_USE_PRIVATE_MSG and not is_private
            target_channel = channel if not use_private else user
            
            if not args:
                # Show context summary
                self.show_context_summary(connection, target_channel)
                if use_private:
                    connection.privmsg(channel, f"📩 Sent context summary to {user} via private message.")
            elif args[0] == 'clear':
                # Clear context for this channel - this should always be public
                self.context_manager.clear_channel_context(channel)
                connection.privmsg(channel, f"🧹 Context cleared for {channel}")
            elif args[0] == 'test' and len(args) > 1:
                # Test context relevance for a query
                query = ' '.join(args[1:])
                self.test_context_relevance(connection, target_channel, query)
                if use_private:
                    connection.privmsg(channel, f"📩 Sent context test results to {user} via private message.")
        
        elif command == 'ask':
            if args:
                # Join all arguments as the question
                question = ' '.join(args)
                self.handle_ask_command(connection, channel, user, question)
            else:
                connection.privmsg(channel, "Usage: !ask <your question>")
    
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
    
    def show_recent_links(self, connection, channel, requesting_user=None):
        """Show recent links in the channel"""
        # If requesting_user is provided, we're sending to them privately about a channel
        source_channel = channel if not requesting_user else self.config.IRC_CHANNEL
        links = self.db.get_recent_links(source_channel, limit=5)
        
        if not links:
            msg = "No links saved yet!"
            if requesting_user:
                msg = f"No links saved in {source_channel} yet!"
            connection.privmsg(channel, msg)
            return
        
        intro_msg = "📚 Recent links:"
        if requesting_user:
            intro_msg = f"📚 Recent links from {source_channel}:"
        connection.privmsg(channel, intro_msg)
        for link in links:
            msg = f"• {link['title']} (by {link['user']}) - {link['url']}"
            if len(msg) > 400:
                msg = msg[:397] + "..."
            connection.privmsg(channel, msg)
    
    def search_links(self, connection, channel, query, requesting_user=None):
        """Search for links matching a query"""
        # If requesting_user is provided, we're sending to them privately about a channel
        source_channel = channel if not requesting_user else self.config.IRC_CHANNEL
        links = self.db.search_links(source_channel, query, limit=3)
        
        if not links:
            msg = f"No links found matching '{query}'"
            if requesting_user:
                msg = f"No links found in {source_channel} matching '{query}'"
            connection.privmsg(channel, msg)
            return
        
        intro_msg = f"🔍 Search results for '{query}':"
        if requesting_user:
            intro_msg = f"🔍 Search results from {source_channel} for '{query}':"
        connection.privmsg(channel, intro_msg)
        for link in links:
            msg = f"• {link['title']} (by {link['user']}) - {link['url']}"
            if len(msg) > 400:
                msg = msg[:397] + "..."
            connection.privmsg(channel, msg)
    
    def show_stats(self, connection, channel, requesting_user=None):
        """Show link statistics"""
        # If requesting_user is provided, we're sending to them privately about a channel
        source_channel = channel if not requesting_user else self.config.IRC_CHANNEL
        stats = self.db.get_link_stats(source_channel)
        
        msg = f"📊 Stats"
        if requesting_user:
            msg += f" for {source_channel}"
        msg += f": {stats.get('total_links', 0)} links saved by {stats.get('unique_users', 0)} users"
        if 'top_contributor' in stats:
            msg += f" (top: {stats['top_contributor']} with {stats['top_contributor_count']} links)"
        
        connection.privmsg(channel, msg)
    
    def show_help(self, connection, channel):
        """Show help information"""
        help_text = [
            "🤖 AircBot Commands:",
            "!links - Show recent links",
            "!links details - Show recent links with timestamps",
            "!links search <term> - Search saved links",
            "!links by <user> - Show links by specific user",
            "!links stats - Show statistics",
            "!ask <question> - Ask the LLM a question",
            "!context - Show context summary",
            "!context clear - Clear context for this channel",
            "!context test <query> - Test context relevance",
            "!ratelimit - Show rate limit status",
            "!performance - Show LLM performance stats",
            "!help - Show this help",
            "I automatically save any links you share!",
            "💡 I now use smart context analysis for better AI responses!",
            f"📩 Most commands send responses privately{' (disabled)' if not self.config.COMMANDS_USE_PRIVATE_MSG else ''}",
            f"💬 !ask responses stay public for community benefit",
            f"💬 You can also message me directly for private conversations{' (disabled)' if not self.config.PRIVATE_MSG_ENABLED else ''}",
            f"Rate limits: {self.config.RATE_LIMIT_USER_PER_MINUTE}/min per user, {self.config.RATE_LIMIT_TOTAL_PER_MINUTE}/min total"
        ]
        
        for line in help_text:
            connection.privmsg(channel, line)
    
    def show_rate_limit_stats(self, connection, channel, user):
        """Show rate limiting statistics"""
        # Get overall stats
        stats = self.rate_limiter.get_stats()
        user_stats = self.rate_limiter.get_user_stats(user)
        
        connection.privmsg(channel, f"⏱️ Rate Limit Status:")
        connection.privmsg(channel, f"• Total requests this minute: {stats['total_requests_this_minute']}/{stats['total_limit']}")
        connection.privmsg(channel, f"• Active users: {stats['active_users']}")
        connection.privmsg(channel, f"• {user}: {user_stats['requests_this_minute']}/{user_stats['limit']} (remaining: {user_stats['remaining']})")
    
    def show_performance_stats(self, connection, channel):
        """Show LLM performance statistics"""
        if not self.llm_handler.is_enabled():
            connection.privmsg(channel, "❌ LLM is not available - no performance stats.")
            return
        
        stats = self.llm_handler.get_performance_stats()
        
        connection.privmsg(channel, f"📊 LLM Performance Stats:")
        connection.privmsg(channel, f"• Total requests: {stats['total_requests']}")
        connection.privmsg(channel, f"• Failed requests: {stats['failed_requests']}")
        connection.privmsg(channel, f"• Success rate: {stats['success_rate']}")
        connection.privmsg(channel, f"• Average response time: {stats['avg_response_time']}")
        connection.privmsg(channel, f"• Response time range: {stats['min_response_time']} - {stats['max_response_time']}")
        connection.privmsg(channel, f"• Recent sample size: {stats['recent_requests']} requests")
    
    def on_disconnect(self, connection, event):
        """Called when disconnected from server"""
        logger.warning(f"Disconnected from IRC server: {event}")
        logger.warning(f"Event type: {event.type}")
        logger.warning(f"Event source: {event.source}")
        logger.warning(f"Event target: {event.target}")
        logger.warning(f"Event arguments: {event.arguments}")
        if hasattr(event, 'error'):
            logger.error(f"Disconnect error: {event.error}")
    
    def on_error(self, connection, event):
        """Called when an error occurs"""
        logger.error(f"IRC Error: {event}")
        logger.error(f"Error type: {event.type}")
        logger.error(f"Error source: {event.source}")
        logger.error(f"Error target: {event.target}")
        logger.error(f"Error arguments: {event.arguments}")
    
    def on_ctcp(self, connection, event):
        """Handle CTCP events"""
        logger.debug(f"CTCP event: {event}")
    
    def on_nicknameinuse(self, connection, event):
        """Handle nickname in use"""
        logger.warning(f"Nickname '{self.config.IRC_NICKNAME}' is in use")
        # Try with underscore
        new_nick = self.config.IRC_NICKNAME + "_"
        logger.info(f"Trying nickname: {new_nick}")
        connection.nick(new_nick)
    
    def on_erroneusnickname(self, connection, event):
        """Handle erroneous nickname"""
        logger.error(f"Erroneous nickname: {event}")
    
    def on_passwdmismatch(self, connection, event):
        """Handle password mismatch"""
        logger.error(f"Password mismatch: {event}")
    
    def on_badchannelkey(self, connection, event):
        """Handle bad channel key"""
        logger.error(f"Bad channel key for {event.target}: {event}")
    
    def on_channelisfull(self, connection, event):
        """Handle channel is full"""
        logger.error(f"Channel {event.target} is full: {event}")
    
    def on_inviteonlychan(self, connection, event):
        """Handle invite only channel"""
        logger.error(f"Channel {event.target} is invite only: {event}")
    
    def on_bannedfromchan(self, connection, event):
        """Handle banned from channel"""
        logger.error(f"Banned from channel {event.target}: {event}")
    
    def on_all_raw_messages(self, connection, event):
        """Log all raw IRC messages for debugging"""
        logger.debug(f"RAW IRC: {event.type} - {event.source} - {event.target} - {event.arguments}")
    
    def show_detailed_links(self, connection, channel, requesting_user=None):
        """Show recent links with detailed information (user, timestamp)"""
        # If requesting_user is provided, we're sending to them privately about a channel
        source_channel = channel if not requesting_user else self.config.IRC_CHANNEL
        links = self.db.get_links_with_details(source_channel, limit=5)
        
        if not links:
            msg = "No links saved yet!"
            if requesting_user:
                msg = f"No links saved in {source_channel} yet!"
            connection.privmsg(channel, msg)
            return
        
        intro_msg = "📚 Recent links (with details):"
        if requesting_user:
            intro_msg = f"📚 Recent links from {source_channel} (with details):"
        connection.privmsg(channel, intro_msg)
        for link in links:
            msg = f"• {link['title']}"
            msg += f" | 👤 {link['user']}"
            msg += f" | 🕐 {link['formatted_time']}"
            msg += f" | 🔗 {link['url']}"
            
            # Split long messages
            if len(msg) > 400:
                connection.privmsg(channel, f"• {link['title']}")
                connection.privmsg(channel, f"  👤 {link['user']} | 🕐 {link['formatted_time']}")
                connection.privmsg(channel, f"  🔗 {link['url']}")
            else:
                connection.privmsg(channel, msg)
    
    def show_links_by_user(self, connection, channel, username, requesting_user=None):
        """Show all links shared by a specific user"""
        # If requesting_user is provided, we're sending to them privately about a channel
        source_channel = channel if not requesting_user else self.config.IRC_CHANNEL
        links = self.db.get_all_links_by_user(source_channel, username)
        
        if not links:
            msg = f"No links found from user '{username}'"
            if requesting_user:
                msg += f" in {source_channel}"
            connection.privmsg(channel, msg)
            return
        
        intro_msg = f"🔍 Links shared by {username}:"
        if requesting_user:
            intro_msg = f"🔍 Links shared by {username} in {source_channel}:"
        connection.privmsg(channel, intro_msg)
        for link in links[:3]:  # Limit to 3 to avoid spam
            msg = f"• {link['title']} | 🕐 {link['formatted_time']} | 🔗 {link['url']}"
            if len(msg) > 400:
                connection.privmsg(channel, f"• {link['title']}")
                connection.privmsg(channel, f"  🕐 {link['formatted_time']} | 🔗 {link['url']}")
            else:
                connection.privmsg(channel, msg)
        
        if len(links) > 3:
            connection.privmsg(channel, f"... and {len(links) - 3} more links")
    
    def handle_ask_command(self, connection, channel, user, question, show_thinking=True):
        """Handle !ask command - query the LLM with optional context"""
        if not self.llm_handler.is_enabled():
            connection.privmsg(channel, "❌ LLM is not available. Check configuration.")
            return
        
        # Indicate we're thinking (unless already shown)
        if show_thinking:
            thinking_msg = get_thinking_message(user, question[:100])
            connection.privmsg(channel, thinking_msg)
        
        # Process in a separate thread to avoid blocking
        thread = Thread(target=self._process_ask_request, 
                      args=(connection, channel, user, question))
        thread.daemon = True
        thread.start()
    
    def _process_ask_request(self, connection, channel, user, question):
        """Process the LLM request in a separate thread"""
        # Start timing the total request processing
        start_time = time.time()
        
        try:
            # Get intelligent context from local message queue
            context_messages = self.context_manager.get_relevant_context(channel, question)
            context_str = ""
            
            if context_messages:
                context_str = self.context_manager.format_context_for_llm(context_messages)
                logger.info(f"Using {len(context_messages)} contextual messages for question: {question[:50]}...")
            else:
                # Fallback to recent context if no relevant messages found
                recent_messages = self.context_manager.get_recent_context(channel, limit=3)
                if recent_messages:
                    context_str = self.context_manager.format_context_for_llm(recent_messages)
                    logger.info(f"Using {len(recent_messages)} recent messages as fallback context")
            
            # Ask the LLM with context
            response = self.llm_handler.ask_llm(question, context_str)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            if response:
                # Clean the response for IRC (remove carriage returns and normalize whitespace)
                cleaned_response = self._clean_response_for_irc(response)
                # Split long responses across multiple messages
                self._send_long_message(connection, channel, f"🤖 {cleaned_response}")
                logger.info(f"Total request processing time for '{question[:30]}...': {total_time:.2f}s")
            else:
                connection.privmsg(channel, "❌ No response from LLM")
                logger.warning(f"No response from LLM for '{question[:30]}...' after {total_time:.2f}s")
                
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error processing ask request '{question[:30]}...' after {total_time:.2f}s: {e}")
            connection.privmsg(channel, f"❌ Error processing request: {str(e)}")
    
    def _clean_response_for_irc(self, response: str) -> str:
        """Clean LLM response for IRC compatibility"""
        # Remove thinking tags that some models include
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Replace various newline characters with spaces
        response = response.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
        
        # Replace multiple spaces with single spaces
        response = re.sub(r'\s+', ' ', response)
        
        # Strip leading/trailing whitespace
        response = response.strip()
        
        return response
    
    def _send_long_message(self, connection, channel, message, max_length=400):
        """Split long messages into multiple IRC messages"""
        if len(message) <= max_length:
            connection.privmsg(channel, message)
            return
        
        # Split on sentences or lines first, then by length
        parts = []
        remaining = message
        
        while remaining:
            if len(remaining) <= max_length:
                parts.append(remaining)
                break
            
            # Try to split at sentence boundary
            split_point = max_length
            for punct in ['. ', '! ', '? ']:
                punct_pos = remaining.rfind(punct, 0, max_length)
                if punct_pos > max_length // 2:  # Don't split too early
                    split_point = punct_pos + len(punct)
                    break
            
            # If no good split point, just cut at max length
            if split_point == max_length:
                split_point = max_length
            
            parts.append(remaining[:split_point])
            remaining = remaining[split_point:].lstrip()
        
        # Send each part
        for i, part in enumerate(parts):
            if i > 0:
                time.sleep(0.5)  # Small delay between messages
            connection.privmsg(channel, part)
    
    def is_bot_mentioned(self, message: str) -> bool:
        """Check if the bot is mentioned in the message"""
        import re
        message_lower = message.lower()
        
        # Get the current nickname (might have _ appended if original was taken)
        current_nick = self.connection.get_nickname().lower()
        
        # Check for various mention patterns with word boundaries
        mention_patterns = [
            rf'\b{re.escape(current_nick)}\b',  # Current nick with word boundaries
            rf'\b{re.escape(self.config.IRC_NICKNAME.lower())}\b',  # Original configured name
            r'\baircbot\b',  # Bot name with word boundaries
            r'\bbot\b',  # Generic bot reference with word boundaries
        ]
        
        # Check if any of the patterns appear in the message
        for pattern in mention_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def handle_name_mention(self, connection, channel, user, message):
        """Handle when the bot is mentioned by name with rate limiting"""
        # Check rate limit
        if not self.rate_limiter.is_allowed(user):
            logger.info(f"Rate limited mention from {user}: {message}")
            connection.privmsg(channel, f"⏱️ {user}: Please wait a moment before mentioning me again.")
            return
        
        # Extract the part of the message that's not the bot name
        message_lower = message.lower()
        current_nick = connection.get_nickname().lower()
        
        # Check for capabilities question in the original message first
        if self._is_asking_for_capabilities(message_lower):
            self._handle_capability_request(connection, channel, user)
            return
        
        # Remove bot name mentions to get the actual question/comment
        clean_message = message
        for pattern in [current_nick, self.config.IRC_NICKNAME.lower(), "aircbot", "bot"]:
            clean_message = clean_message.replace(pattern, "").replace(pattern.title(), "")
        
        # Clean up punctuation and whitespace
        clean_message = clean_message.strip(" ,:;!?")
        clean_message_lower = clean_message.lower()
        
        if clean_message and len(clean_message) > 3:  # If there's a meaningful question/comment
            # Check if they're asking about capabilities first
            if self._is_asking_for_capabilities(clean_message_lower):
                self._handle_capability_request(connection, channel, user)
            # Check if they're asking for links
            elif self._is_asking_for_links(clean_message_lower):
                self._handle_links_request(connection, channel, clean_message_lower)
            else:
                # Treat it as an ask command
                thinking_msg = get_thinking_message(user, clean_message[:100])
                connection.privmsg(channel, thinking_msg)
                self.handle_ask_command(connection, channel, user, clean_message, show_thinking=False)
        else:
            # Just a mention without a question - provide help
            responses = [
                f"Hi {user}! I'm here to help. Try !ask <question> or !help for commands.",
                f"Yes {user}? I can answer questions with !ask or save your links automatically.",
                f"Hello {user}! Use !help to see what I can do, or just ask me something with !ask.",
            ]
            import random
            response = random.choice(responses)
            connection.privmsg(channel, response)
    
    def _is_asking_for_capabilities(self, message: str) -> bool:
        """Check if the user is asking about the bot's capabilities or what it can do"""
        capability_phrases = [
            "what can you do", "what do you do", "what are you for",
            "what are your capabilities", "what are your features",
            "what can you help with", "what can you help me with",
            "how can you help", "what commands", "what functions",
            "what are your commands", "what are your functions",
            "help me", "show help", "tell me what you do",
            "what's your purpose", "what is your purpose",
            "how do you work", "what do you offer"
        ]
        
        message_lower = message.lower().strip()
        
        # Check for exact or partial matches
        for phrase in capability_phrases:
            if phrase in message_lower:
                return True
        
        # Check if it's just "help" or "capabilities"
        stripped = message_lower.strip(" ?!.,;:")
        if stripped in ["help", "capabilities", "commands", "functions", "purpose"]:
            return True
            
        return False
    
    def _is_asking_for_links(self, message: str) -> bool:
        """Check if the user is asking for links"""
        # Check for explicit compound phrases first (these are always link requests)
        explicit_phrases = [
            "saved links", "recent links", "show links", "get links", 
            "list links", "what links", "any links", "share links",
            "links you saved", "links you have", "links stats",
            "links statistics", "detailed links"
        ]
        
        for phrase in explicit_phrases:
            if phrase in message:
                return True
        
        # Check if message is just "links" or "links?" - treat as request
        stripped = message.strip(" ?!.,;:")
        if stripped == "links" or stripped == "link":
            return True
        
        # For single word "links", need to have action words AND proper context
        if "links" in message:
            action_words = ["show", "get", "give", "list", "what", "any", "have", "share", "find", "search", "stats", "statistics", "detailed", "need", "want"]
            has_action_word = any(word in message for word in action_words)
            
            if has_action_word:
                # Check for question/request patterns
                patterns = [
                    r'(?:what|any|show|get|have|share|find|search|need|want).*\blinks?\b',
                    r'\blinks?\b.*(?:you|saved|recent|have|stats|statistics|detailed)',
                    r'(?:stats|statistics|detailed).*\blinks?\b'
                ]
                
                import re
                for pattern in patterns:
                    if re.search(pattern, message):
                        return True
                        
        return False
    
    def _handle_links_request(self, connection, channel, message: str):
        """Handle different types of link requests"""
        # Parse the request to determine what type of links command to run
        if any(word in message for word in ["search", "find", "look for"]):
            # Extract search term
            import re
            # Look for search patterns like "search for X" or "find X links"
            search_match = re.search(r'(?:search|find|look for)\s+(.+?)(?:\s+links?|$)', message)
            if search_match:
                search_term = search_match.group(1).strip()
                self.search_links(connection, channel, search_term)
                return
        
        if any(word in message for word in ["by", "from", "user", "shared by"]):
            # Extract username
            import re
            user_match = re.search(r'(?:by|from|shared by)\s+(\w+)', message)
            if user_match:
                username = user_match.group(1)
                self.show_links_by_user(connection, channel, username)
                return
        
        if any(word in message for word in ["stats", "statistics", "count", "how many"]):
            self.show_stats(connection, channel)
            return
        
        if any(word in message for word in ["details", "detailed", "timestamps", "when"]):
            self.show_detailed_links(connection, channel)
            return
        
        # Default to showing recent links
        self.show_recent_links(connection, channel)
    
    def _handle_capability_request(self, connection, channel, user):
        """Handle requests about the bot's capabilities"""
        capability_messages = [
            f"🤖 Hi {user}! Here's what I can do:",
            "📎 I automatically save any links you share in the channel",
            "💬 You can mention me or ask me questions and I'll respond using AI",
            "🔍 Link management commands:",
            "  • !links - Show recent links",
            "  • !links search <term> - Search saved links",
            "  • !links by <user> - Show links by specific user",
            "  • !links stats - Show statistics",
            "  • !links details - Show recent links with timestamps",
            "🤖 AI commands:",
            "  • !ask <question> - Ask me anything",
            "  • Just mention my name and ask a question",
            "📊 Utility commands:",
            "  • !ratelimit - Check rate limit status",
            "  • !performance - Show AI performance stats",
            "  • !help - Show command help",
            f"📩 Most commands send responses privately to keep the channel clean",
            f"💬 !ask responses stay public for everyone's benefit",
            f"⚡ Rate limits: {self.config.RATE_LIMIT_USER_PER_MINUTE}/min per user, {self.config.RATE_LIMIT_TOTAL_PER_MINUTE}/min total"
        ]
        
        for msg in capability_messages:
            connection.privmsg(channel, msg)
            time.sleep(0.3)  # Small delay between messages to avoid flooding
    
    def show_context_summary(self, connection, channel):
        """Show context summary for the current channel"""
        summary = self.context_manager.get_context_summary(channel)
        
        if summary['total_messages'] == 0:
            connection.privmsg(channel, "📝 No messages in context queue yet.")
            return
        
        # Format timestamps
        import datetime
        oldest = datetime.datetime.fromtimestamp(summary['oldest_timestamp']).strftime("%H:%M")
        newest = datetime.datetime.fromtimestamp(summary['newest_timestamp']).strftime("%H:%M")
        
        connection.privmsg(channel, f"📝 Context Summary for {channel}:")
        connection.privmsg(channel, f"• Messages in queue: {summary['total_messages']}/{self.config.MESSAGE_QUEUE_SIZE}")
        connection.privmsg(channel, f"• Unique users: {summary['unique_users']}")
        connection.privmsg(channel, f"• Commands: {summary['commands']}")
        connection.privmsg(channel, f"• Bot mentions: {summary['bot_mentions']}")
        connection.privmsg(channel, f"• Time range: {oldest} - {newest}")
        connection.privmsg(channel, f"• Context analysis: {'enabled' if self.config.CONTEXT_ANALYSIS_ENABLED else 'disabled'}")
        connection.privmsg(channel, f"• Relevance threshold: {self.config.CONTEXT_RELEVANCE_THRESHOLD}")
    
    def test_context_relevance(self, connection, channel, query):
        """Test context relevance for a given query"""
        if not self.config.CONTEXT_ANALYSIS_ENABLED:
            connection.privmsg(channel, "❌ Context analysis is disabled")
            return
        
        # Get relevant context
        relevant_messages = self.context_manager.get_relevant_context(channel, query, max_messages=5)
        
        if not relevant_messages:
            connection.privmsg(channel, f"🔍 No relevant context found for: '{query}'")
            return
        
        connection.privmsg(channel, f"🔍 Found {len(relevant_messages)} relevant messages for: '{query}'")
        
        for i, msg in enumerate(relevant_messages, 1):
            # Calculate age
            age_minutes = (time.time() - msg.timestamp) / 60
            if age_minutes < 1:
                age_str = "just now"
            elif age_minutes < 60:
                age_str = f"{int(age_minutes)}m ago"
            else:
                age_str = f"{int(age_minutes/60)}h ago"
            
            # Truncate message for display
            content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
            connection.privmsg(channel, f"  {i}. [{age_str}] {msg.user}: {content}")

def main():
    """Main entry point"""
    try:
        bot = AircBot()
        logger.info("Starting bot...")
        logger.info(f"Attempting to connect to {bot.config.IRC_SERVER}:{bot.config.IRC_PORT}")
        logger.info(f"Using SSL: {bot.config.IRC_USE_SSL}")
        logger.info(f"SSL verification: {bot.config.IRC_SSL_VERIFY}")
        bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot crashed with exception: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
