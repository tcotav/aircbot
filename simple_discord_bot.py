#!/usr/bin/env python3
"""
AircBot Discord - Simple Discord Bot with Link Memory
A Discord bot that captures and saves links shared in channels.
"""

import asyncio
import logging
import os
import sys
import random
import re
from typing import List, Dict, Optional

import discord
from dotenv import load_dotenv

from config import Config
from database import Database
from link_handler import LinkHandler
from llm_handler import LLMHandler
from rate_limiter import RateLimiter
from prompts import get_thinking_message
from context_manager import ContextManager
from content_filter import ContentFilter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDiscordBot(discord.Client):
    def __init__(self):
        """Initialize the Discord bot with components"""
        # Configure Discord intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(intents=intents)
        
        # Initialize components (reusing existing IRC bot components)
        self.config = Config()
        self.db = Database(self.config.DATABASE_PATH)
        self.link_handler = LinkHandler()
        self.llm_handler = LLMHandler(self.config)
        self.rate_limiter = RateLimiter(
            user_limit_per_minute=self.config.RATE_LIMIT_USER_PER_MINUTE,
            total_limit_per_minute=self.config.RATE_LIMIT_TOTAL_PER_MINUTE
        )
        self.context_manager = ContextManager(self.config)
        
        # Initialize content filter (after LLM handler so it can use local LLM)
        self.content_filter = ContentFilter(self.config, self.llm_handler)
        
        logger.info("Simple Discord bot initialized")

    async def setup_hook(self):
        """Called when the client is done preparing the data received from Discord"""
        logger.info("Bot setup hook called")

    async def on_ready(self):
        """Event handler for when the bot has connected to Discord"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guild(s)')

    async def on_message(self, message):
        """Handle incoming messages"""
        # Don't respond to ourselves or other bots
        if message.author == self.user or message.author.bot:
            return
        
        # Get message details
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "DM"
        user = str(message.author)
        content = message.content
        
        # Determine message type for context
        is_command = content.startswith('!')
        is_bot_mention = self.user.mentioned_in(message)
        
        # Add message to local context queue
        self.context_manager.add_message(user, channel_name, content, is_command, is_bot_mention)
        
        # Save message to database if enabled
        if self.config.SAVE_MESSAGES_TO_DB:
            self.db.save_message(user, channel_name, content)
        
        # Handle different message types
        if content.startswith('!'):
            await self.handle_command(message)
        elif is_bot_mention:
            await self.handle_mention(message)
        
        # Extract and process links
        await self.process_links(message)

    async def handle_command(self, message):
        """Handle bot commands"""
        user = str(message.author)
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(user):
            await message.channel.send(f"⏱️ {message.author.mention}: Please wait a moment before sending another command.")
            return
        
        # Parse command
        parts = message.content[1:].split()  # Remove ! and split
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Route to appropriate handler
        if command == 'bothelp':
            await self.show_help(message)
        elif command == 'links':
            await self.handle_links_command(message, args)
        elif command == 'ask':
            if args:
                question = ' '.join(args)
                await self.handle_ask_command(message, question)
            else:
                await message.channel.send("Usage: !ask <your question>")
        else:
            await message.channel.send(f"Unknown command: {command}. Try !bothelp")

    async def handle_links_command(self, message, args: List[str]):
        """Handle links command variations"""
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "DM"
        
        if not args:
            # Show recent links
            links = self.db.get_recent_links(channel_name, limit=5)
            if not links:
                await message.channel.send("No links saved yet!")
                return
            
            response = "📚 Recent links:\n"
            for link in links:
                line = f"• {link['title']} (by {link['user']}) - {link['url']}"
                if len(line) > 100:
                    line = line[:97] + "..."
                response += line + "\n"
            
            await message.channel.send(response)
        
        elif args[0] == "search" and len(args) > 1:
            query = ' '.join(args[1:])
            links = self.db.search_links(channel_name, query, limit=3)
            if not links:
                await message.channel.send(f"No links found matching '{query}'")
                return
            
            response = f"🔍 Search results for '{query}':\n"
            for link in links:
                line = f"• {link['title']} (by {link['user']}) - {link['url']}"
                response += line + "\n"
            
            await message.channel.send(response)
        
        elif args[0] == "stats":
            stats = self.db.get_link_stats(channel_name)
            response = f"📊 Stats: {stats.get('total_links', 0)} links saved by {stats.get('unique_users', 0)} users"
            if 'top_contributor' in stats:
                response += f" (top: {stats['top_contributor']} with {stats['top_contributor_count']} links)"
            await message.channel.send(response)
        else:
            # Handle unknown subcommands or invalid syntax
            if args[0] == "search" and len(args) == 1:
                await message.channel.send("Usage: !links search <search term>")
            else:
                await message.channel.send(f"Unknown links command: {args[0]}\nValid options: !links, !links search <term>, !links stats")


    async def handle_ask_command(self, message, question: str):
        """Handle AI ask command"""
        if not self.llm_handler.is_enabled():
            await message.channel.send("❌ LLM is not available. Check configuration.")
            return
        
        user = str(message.author)
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "DM"
        
        # Filter content
        filter_result = self.content_filter.filter_content(question, user, channel_name)
        if not filter_result.is_allowed:
            await message.channel.send(f"❌ {message.author.mention}: Your message cannot be processed. Please keep discussions appropriate.")
            return
        
        # Show thinking message
        thinking_msg = get_thinking_message(user, question[:100])
        await message.channel.send(thinking_msg)
        
        try:
            # Get context
            context_messages = self.context_manager.get_relevant_context(channel_name, question)
            context_str = ""
            if context_messages:
                context_str = self.context_manager.format_context_for_llm(context_messages)
            
            # Ask LLM (run in executor to avoid blocking)
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.llm_handler.ask_llm, question, context_str
            )
            
            if response:
                # Clean response for Discord
                cleaned_response = self.clean_response_for_discord(response)
                await message.channel.send(f"🤖 {cleaned_response}")
            else:
                await message.channel.send("❌ No response from LLM")
                
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            await message.channel.send(f"❌ Error processing request: {str(e)}")

    async def handle_mention(self, message):
        """Handle when bot is mentioned"""
        user = str(message.author)
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(user):
            await message.channel.send(f"⏱️ {message.author.mention}: Please wait a moment before mentioning me again.")
            return
        
        # Extract content without mentions
        content = message.content
        for mention in message.mentions:
            if mention == self.user:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
        
        content = content.strip()
        
        if content and len(content) > 3:
            # Treat as ask command
            await self.handle_ask_command(message, content)
        else:
            # Default greeting responses
            responses = [
                f"Hi {message.author.mention}! Try !ask <question> or !bothelp for commands.",
                f"Hello {message.author.mention}! Use !bothelp to see what I can do.",
            ]
            await message.channel.send(random.choice(responses))

    async def process_links(self, message):
        """Process links in messages"""
        links = self.link_handler.extract_urls(message.content)
        if links:
            for url in links:
                try:
                    # Get metadata (run in executor to avoid blocking)
                    title, description = await asyncio.get_event_loop().run_in_executor(
                        None, self.link_handler.get_link_metadata, url
                    )
                    
                    # Save to database
                    channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "DM"
                    user = str(message.author)
                    saved = self.db.save_link(url, title, description, user, channel_name)
                    
                    if saved:
                        response = f"📎 Saved: {title}"
                        if len(response) > 1900:
                            response = response[:1897] + "..."
                        await message.channel.send(response)
                        logger.info(f"Saved link: {url} - {title}")
                        
                except Exception as e:
                    logger.error(f"Error processing link {url}: {e}")

    async def show_help(self, message):
        """Show help information"""
        help_text = """
🤖 **AircBot Discord Commands**

**Link Management:**
• `!links` - Show recent links
• `!links search <term>` - Search for links
• `!links stats` - Show link statistics

**AI Features:**
• `!ask <question>` - Ask me anything
• Mention me directly to chat

**Other:**
• `!bothelp` - Show this help message

💡 I automatically save any links you share in chat!
"""
        await message.channel.send(help_text)

    def clean_response_for_discord(self, response: str) -> str:
        """Clean LLM response for Discord"""
        # Remove thinking tags
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Clean up extra whitespace
        response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
        response = re.sub(r'[ \t]+', ' ', response)
        response = response.strip()
        
        # Truncate if too long for Discord
        if len(response) > 1900:
            response = response[:1897] + "..."
        
        return response

async def main():
    """Main entry point"""
    config = Config()
    
    # Check token
    discord_token = getattr(config, 'DISCORD_TOKEN', None)
    if not discord_token:
        logger.error("DISCORD_TOKEN not found in configuration.")
        sys.exit(1)
    
    # Create bot
    bot = SimpleDiscordBot()
    
    try:
        logger.info("Starting simple Discord bot...")
        async with bot:
            await bot.start(discord_token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        await bot.close()
        raise
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
