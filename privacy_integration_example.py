#!/usr/bin/env python3
"""
Example integration of privacy filter with context manager
This shows how the privacy filtering would work in practice
"""

from context_manager import ContextManager, Message
from privacy_filter import PrivacyFilter, PrivacyConfig
from typing import List, Set
import logging
import time

logger = logging.getLogger(__name__)

class PrivacyAwareContextManager(ContextManager):
    """Extended context manager with privacy protection"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Initialize privacy filter
        privacy_config = PrivacyConfig(
            max_channel_users=config.PRIVACY_MAX_CHANNEL_USERS,
            username_anonymization=config.PRIVACY_USERNAME_ANONYMIZATION,
            pii_detection=config.PRIVACY_PII_DETECTION,
            preserve_conversation_flow=config.PRIVACY_PRESERVE_CONVERSATION_FLOW,
            privacy_level=config.PRIVACY_LEVEL
        )
        
        self.privacy_filter = PrivacyFilter(privacy_config) if config.PRIVACY_FILTER_ENABLED else None
    
    def get_channel_users(self, channel: str) -> Set[str]:
        """Get all known users from the channel's message queue"""
        if channel not in self.message_queues:
            return set()
        
        return {msg.user for msg in self.message_queues[channel]}
    
    def format_context_for_llm(self, messages: List[Message]) -> str:
        """Format a list of messages for inclusion in LLM context with privacy protection"""
        if not messages:
            return ""
        
        # Get channel and known users
        channel = messages[0].channel
        known_users = {msg.user for msg in messages}
        
        formatted_lines = []
        formatted_lines.append("Recent conversation context:")
        
        for msg in messages:
            # Format timestamp as relative time
            age_minutes = (time.time() - msg.timestamp) / 60
            if age_minutes < 1:
                time_str = "just now"
            elif age_minutes < 60:
                time_str = f"{int(age_minutes)}m ago"
            else:
                hours = int(age_minutes / 60)
                time_str = f"{hours}h ago"
            
            # Apply privacy filtering if enabled
            if self.privacy_filter:
                sanitized_content, anonymous_username = self.privacy_filter.sanitize_for_llm(
                    msg.content, msg.user, channel, known_users
                )
            else:
                sanitized_content = msg.content
                anonymous_username = msg.user
            
            # Add context indicators
            indicators = []
            if msg.is_command:
                indicators.append("cmd")
            if msg.is_bot_mention:
                indicators.append("@bot")
            
            indicator_str = f" [{','.join(indicators)}]" if indicators else ""
            
            formatted_lines.append(f"[{time_str}] {anonymous_username}{indicator_str}: {sanitized_content}")
        
        return "\n".join(formatted_lines)
    
    def get_privacy_stats(self, channel: str) -> dict:
        """Get privacy statistics for a channel"""
        if not self.privacy_filter:
            return {"privacy_enabled": False}
        
        stats = self.privacy_filter.get_privacy_stats(channel)
        stats["privacy_enabled"] = True
        return stats

# Example usage and testing
def example_privacy_scenarios():
    """Show examples of how privacy filtering handles different scenarios"""
    
    class MockConfig:
        PRIVACY_FILTER_ENABLED = True
        PRIVACY_MAX_CHANNEL_USERS = 20
        PRIVACY_USERNAME_ANONYMIZATION = True
        PRIVACY_PII_DETECTION = True
        PRIVACY_PRESERVE_CONVERSATION_FLOW = True
        PRIVACY_LEVEL = 'medium'
    
    config = MockConfig()
    privacy_config = PrivacyConfig(
        max_channel_users=config.PRIVACY_MAX_CHANNEL_USERS,
        username_anonymization=config.PRIVACY_USERNAME_ANONYMIZATION,
        pii_detection=config.PRIVACY_PII_DETECTION,
        preserve_conversation_flow=config.PRIVACY_PRESERVE_CONVERSATION_FLOW,
        privacy_level=config.PRIVACY_LEVEL
    )
    
    privacy_filter = PrivacyFilter(privacy_config)
    
    # Scenario 1: Direct addressing with common word username
    known_users = {'rain', 'developer', 'admin'}
    content1 = "rain, you don't know what you're talking about"
    sanitized1, anon_user1 = privacy_filter.sanitize_for_llm(content1, 'developer', '#test', known_users)
    print(f"Original: {content1}")
    print(f"Sanitized: {sanitized1}")
    print(f"Author: developer -> {anon_user1}")
    print()
    
    # Scenario 2: Technical discussion with PII
    content2 = "My email is john@example.com and my phone is 555-123-4567"
    sanitized2, anon_user2 = privacy_filter.sanitize_for_llm(content2, 'john', '#tech', known_users)
    print(f"Original: {content2}")
    print(f"Sanitized: {sanitized2}")
    print()
    
    # Scenario 3: Weather discussion with username "rain"
    content3 = "I think it's going to rain tomorrow"
    sanitized3, anon_user3 = privacy_filter.sanitize_for_llm(content3, 'weatherguy', '#general', known_users)
    print(f"Original: {content3}")
    print(f"Sanitized: {sanitized3}")
    print(f"(Note: 'rain' NOT replaced because it's not addressing the user)")
    print()
    
    # Scenario 4: Large channel (privacy skipped)
    large_users = {f'user{i}' for i in range(25)}  # 25 users > 20 limit
    content4 = "user5, can you help me with this?"
    privacy_filter.config.max_channel_users = 20
    sanitized4, anon_user4 = privacy_filter.sanitize_for_llm(content4, 'user10', '#largechannel', large_users)
    print(f"Large channel scenario:")
    print(f"Original: {content4}")
    print(f"Sanitized: {sanitized4}")
    print(f"(Note: Privacy skipped due to channel size: {len(large_users)} > 20)")

if __name__ == "__main__":
    example_privacy_scenarios()
