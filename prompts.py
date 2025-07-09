#!/usr/bin/env python3
"""
Prompts and system messages for the IRC bot
"""

from typing import Optional
import logging


class PromptTemplates:
    """Collection of prompt templates for the LLM"""
    
    @staticmethod
    def get_system_prompt(bot_name: str, context: Optional[str] = None, config=None) -> str:
        """
        Get the system prompt for the LLM
        
        Args:
            bot_name: The name of the bot
            context: Optional recent channel context
            config: Config object for personality settings
            
        Returns:
            Formatted system prompt
        """
        # Check if personality prompt is enabled and available
        if config and config.PERSONALITY_ENABLED:
            try:
                with open(config.PERSONALITY_PROMPT_FILE, 'r', encoding='utf-8') as f:
                    personality_prompt = f.read().strip()
                    
                # Use personality prompt as the base, but still include bot name
                base_prompt = f"You are {bot_name}. {personality_prompt}"
                
            except Exception as e:
                # Log error but fall back to default prompt
                logger = logging.getLogger(__name__)
                logger.error(f"Error reading personality prompt file: {e}")
                # Fall back to default prompt
                base_prompt = (
                    f"You are {bot_name}, a friendly IRC bot. "
                    "Give direct, concise answers without any thinking process or reasoning. "
                    "Do not use <think> tags or explain your thought process. "
                    "Answer immediately and briefly. "
                    "Example: User says 'hello' -> You say 'Hi there!' "
                    "User says 'how are you?' -> You say 'I'm great, thanks!' "
                    "User says 'name three mountain ranges' -> You say 'The Rocky Mountains, Sierra Nevada, and Cascade Range.' "
                    "Keep responses 1-3 sentences max. No thinking, just direct answers."
                )
        else:
            # Default prompt when personality is disabled
            base_prompt = (
                f"You are {bot_name}, a friendly IRC bot. "
                "Give direct, concise answers without any thinking process or reasoning. "
                "Do not use <think> tags or explain your thought process. "
                "Answer immediately and briefly. "
                "Example: User says 'hello' -> You say 'Hi there!' "
                "User says 'how are you?' -> You say 'I'm great, thanks!' "
                "User says 'name three mountain ranges' -> You say 'The Rocky Mountains, Sierra Nevada, and Cascade Range.' "
                "Keep responses 1-3 sentences max. No thinking, just direct answers."
            )
        
        if context:
            return f"{base_prompt}\n\nRecent context:\n{context}"
        
        return base_prompt
    
    @staticmethod
    def get_thinking_message(user: str, question: str) -> str:
        """
        Get the thinking message to show while processing
        
        Args:
            user: Username who asked the question
            question: The question being processed
            
        Returns:
            Formatted thinking message
        """
        return f"🤔 Thinking about {user}'s question: {question}"
    
    @staticmethod
    def get_error_messages() -> dict:
        """
        Get common error messages
        
        Returns:
            Dictionary of error message types
        """
        return {
            'llm_unavailable': "❌ LLM is not available",
            'llm_error': "❌ Error calling LLM: {}",
            'too_complex': "That's too complicated to answer here",
            'no_response': "I'm not sure how to respond to that.",
            'rate_limited': "⏰ Slow down! You're asking too many questions. Try again in a minute.",
            'total_rate_limited': "⏰ Too many questions being asked right now. Please wait a moment.",
            'openai_limit_reached': "🚫 Daily OpenAI usage limit reached. Try again tomorrow or ask something simpler for local AI."
        }
    
    @staticmethod
    def get_name_response(bot_name: str) -> str:
        """
        Get response for name questions
        
        Args:
            bot_name: The bot's name
            
        Returns:
            Name response
        """
        return f"I'm {bot_name}!"
    
    @staticmethod
    def get_help_messages() -> dict:
        """
        Get help messages for commands
        
        Returns:
            Dictionary of help messages
        """
        return {
            'main_help': (
                "Available commands: !help, !ask <question>, !links [search], "
                "!latest [count], !stats, !ratelimit, !ping"
            ),
            'ask_help': "Usage: !ask <question> - Ask me anything!",
            'links_help': (
                "Usage: !links [search_term] - Show recent links, optionally filtered by search term"
            ),
            'latest_help': "Usage: !latest [count] - Show the most recent links (default: 5)",
            'stats_help': "Show statistics about saved links",
            'ratelimit_help': "Show your current rate limit status",
            'ping_help': "Check if the bot is responsive"
        }


# Convenience functions for backward compatibility
def get_system_prompt(bot_name: str, context: Optional[str] = None, config=None) -> str:
    """Get system prompt (convenience function)"""
    return PromptTemplates.get_system_prompt(bot_name, context, config)


def get_thinking_message(user: str, question: str) -> str:
    """Get thinking message (convenience function)"""
    return PromptTemplates.get_thinking_message(user, question)


def get_error_message(error_type: str, *args) -> str:
    """Get error message (convenience function)"""
    messages = PromptTemplates.get_error_messages()
    if error_type in messages:
        if args:
            return messages[error_type].format(*args)
        return messages[error_type]
    return f"Unknown error: {error_type}"


def get_name_response(bot_name: str) -> str:
    """Get name response (convenience function)"""
    return PromptTemplates.get_name_response(bot_name)


def get_help_message(command: str = 'main_help') -> str:
    """Get help message (convenience function)"""
    messages = PromptTemplates.get_help_messages()
    return messages.get(command, messages['main_help'])
