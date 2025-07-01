#!/usr/bin/env python3
"""
Privacy Filter for protecting user information sent to LLMs
Handles usernames, PII, and conversational context intelligently
"""

import re
import hashlib
import logging
from typing import Dict, Set, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class PrivacyConfig:
    """Configuration for privacy filtering"""
    max_channel_users: int = 20  # Skip privacy for channels with too many users (performance)
    username_anonymization: bool = True
    pii_detection: bool = True
    preserve_conversation_flow: bool = True  # Try to maintain addressing context
    privacy_level: str = 'medium'  # none, low, medium, high, paranoid

class PrivacyFilter:
    """Intelligent privacy filter for protecting user information"""
    
    def __init__(self, config: PrivacyConfig):
        self.config = config
        self.username_mappings: Dict[str, Dict[str, str]] = defaultdict(dict)  # channel -> {real_user: anon_user}
        self.user_counters: Dict[str, int] = defaultdict(int)  # channel -> counter
        self.channel_users: Dict[str, Set[str]] = defaultdict(set)  # channel -> active users
        
        # Common word usernames that need special handling
        self.common_words = {
            'rain', 'dog', 'cat', 'sun', 'moon', 'fire', 'water', 'wind', 'earth',
            'red', 'blue', 'green', 'black', 'white', 'light', 'dark', 'hope',
            'dream', 'peace', 'love', 'storm', 'cloud', 'star', 'sky', 'ocean'
        }
        
        # PII detection patterns
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'url_with_user': r'https?://(?:github\.com|gitlab\.com)/([^/\s]+)',
        }
    
    def should_apply_privacy(self, channel: str, active_users: Set[str]) -> bool:
        """Determine if privacy filtering should be applied based on channel size"""
        if self.config.privacy_level == 'none':
            return False
        
        # Skip privacy for very large channels (performance consideration)
        if len(active_users) > self.config.max_channel_users:
            logger.info(f"Skipping privacy filtering for {channel}: {len(active_users)} users > {self.config.max_channel_users} limit")
            return False
        
        return True
    
    def update_channel_users(self, channel: str, username: str):
        """Update the active users list for a channel"""
        self.channel_users[channel].add(username)
    
    def get_anonymous_username(self, channel: str, username: str) -> str:
        """Get or create an anonymous username mapping"""
        if username not in self.username_mappings[channel]:
            self.user_counters[channel] += 1
            self.username_mappings[channel][username] = f"User{self.user_counters[channel]}"
        
        return self.username_mappings[channel][username]
    
    def detect_addressing_pattern(self, content: str, known_users: Set[str]) -> List[Tuple[str, int, int]]:
        """
        Detect when someone is addressing another user directly
        Returns list of (username, start_pos, end_pos) for addressing patterns
        """
        addressing_patterns = []
        
        # Pattern 1: "username," at start of message
        for user in known_users:
            pattern = rf'\b{re.escape(user)},\s'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                addressing_patterns.append((user, match.start(), match.end() - 2))  # Don't include ", "
        
        # Pattern 2: "@username" mentions
        for user in known_users:
            pattern = rf'@{re.escape(user)}\b'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                addressing_patterns.append((user, match.start() + 1, match.end()))  # Don't include "@"
        
        return addressing_patterns
    
    def anonymize_content(self, content: str, channel: str, known_users: Set[str]) -> str:
        """Anonymize content while preserving conversational flow"""
        if not self.config.username_anonymization:
            return content
        
        # Get addressing patterns first
        addressing_patterns = self.detect_addressing_pattern(content, known_users)
        
        # Sort by position (reverse order for replacement)
        addressing_patterns.sort(key=lambda x: x[1], reverse=True)
        
        # Replace addressing patterns with anonymous usernames
        anonymized_content = content
        for username, start, end in addressing_patterns:
            anon_username = self.get_anonymous_username(channel, username)
            anonymized_content = anonymized_content[:start] + anon_username + anonymized_content[end:]
        
        # Handle common word usernames more carefully
        # Only replace if they appear in username-like contexts
        for user in known_users:
            if user.lower() in self.common_words:
                # Only replace if it appears in typical username contexts
                # e.g., at start of line, after certain punctuation, etc.
                patterns = [
                    rf'^{re.escape(user)}\s*:',  # IRC-style "username:"
                    rf'\b{re.escape(user)}\b(?=\s+(?:said|says|mentioned|asked|thinks))',  # "rain said..."
                ]
                
                for pattern in patterns:
                    anon_username = self.get_anonymous_username(channel, user)
                    anonymized_content = re.sub(pattern, anon_username, anonymized_content, flags=re.IGNORECASE)
        
        # Handle regular usernames (non-common words)
        for user in known_users:
            if user.lower() not in self.common_words:
                anon_username = self.get_anonymous_username(channel, user)
                # Replace all instances of this username
                anonymized_content = re.sub(rf'\b{re.escape(user)}\b', anon_username, anonymized_content, flags=re.IGNORECASE)
        
        return anonymized_content
    
    def detect_and_replace_pii(self, content: str) -> str:
        """Detect and replace various types of PII"""
        if not self.config.pii_detection:
            return content
        
        protected_content = content
        
        for pii_type, pattern in self.pii_patterns.items():
            replacement = f"[{pii_type.upper()}]"
            protected_content = re.sub(pattern, replacement, protected_content, flags=re.IGNORECASE)
        
        return protected_content
    
    def sanitize_for_llm(self, content: str, username: str, channel: str, known_users: Set[str]) -> Tuple[str, str]:
        """
        Main method to sanitize content for LLM consumption
        
        Args:
            content: Message content
            username: Author username  
            channel: Channel name
            known_users: Set of known usernames in channel
            
        Returns:
            Tuple of (sanitized_content, anonymous_username)
        """
        # Update channel users
        self.update_channel_users(channel, username)
        
        # Check if we should apply privacy
        if not self.should_apply_privacy(channel, known_users):
            return content, username
        
        # Step 1: Replace PII
        protected_content = self.detect_and_replace_pii(content)
        
        # Step 2: Anonymize usernames while preserving conversation flow
        anonymized_content = self.anonymize_content(protected_content, channel, known_users)
        
        # Step 3: Get anonymous username for the author
        anonymous_username = self.get_anonymous_username(channel, username) if self.config.username_anonymization else username
        
        return anonymized_content, anonymous_username
    
    def get_privacy_stats(self, channel: str) -> Dict:
        """Get privacy filtering statistics for a channel"""
        active_users = len(self.channel_users[channel])
        mapped_users = len(self.username_mappings[channel])
        
        return {
            'active_users': active_users,
            'mapped_users': mapped_users,
            'privacy_applied': active_users <= self.config.max_channel_users,
            'privacy_level': self.config.privacy_level,
            'max_channel_users': self.config.max_channel_users
        }
    
    def clear_channel_data(self, channel: str):
        """Clear privacy data for a channel (useful for testing or reset)"""
        if channel in self.username_mappings:
            del self.username_mappings[channel]
        if channel in self.user_counters:
            del self.user_counters[channel]
        if channel in self.channel_users:
            del self.channel_users[channel]
