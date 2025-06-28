#!/usr/bin/env python3
"""
Context Manager for IRC Bot Message Context
Handles local message queues and intelligent context relevance detection
"""

import time
import re
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Represents a chat message with metadata"""
    user: str
    channel: str
    content: str
    timestamp: float
    is_command: bool = False
    is_bot_mention: bool = False

class ContextManager:
    """Manages message context for intelligent LLM interactions"""
    
    def __init__(self, config):
        self.config = config
        # Channel -> deque of Message objects
        self.message_queues: Dict[str, deque] = {}
        
        # Compile regex patterns for efficiency
        self._question_patterns = [
            re.compile(r'\b(?:what|why|how|when|where|who|which|can|could|would|should|is|are|was|were|do|does|did)\b', re.IGNORECASE),
            re.compile(r'\?', re.IGNORECASE),
            re.compile(r'\b(?:explain|tell me|show me|help|describe|define)\b', re.IGNORECASE),
        ]
        
        # Keywords that indicate technical/informational context
        self._technical_keywords = [
            'code', 'programming', 'python', 'javascript', 'error', 'bug', 'function', 'method',
            'class', 'variable', 'database', 'server', 'api', 'http', 'ssl', 'github', 'git',
            'install', 'configuration', 'config', 'setup', 'deployment', 'docker', 'kubernetes',
            'algorithm', 'data', 'structure', 'framework', 'library', 'package', 'module',
            'syntax', 'compile', 'debug', 'test', 'testing', 'performance', 'optimization',
            'security', 'authentication', 'authorization', 'encryption', 'hash', 'token'
        ]
    
    def add_message(self, user: str, channel: str, content: str, is_command: bool = False, is_bot_mention: bool = False):
        """Add a message to the channel's queue"""
        # Initialize queue for new channels
        if channel not in self.message_queues:
            self.message_queues[channel] = deque(maxlen=self.config.MESSAGE_QUEUE_SIZE)
        
        message = Message(
            user=user,
            channel=channel,
            content=content,
            timestamp=time.time(),
            is_command=is_command,
            is_bot_mention=is_bot_mention
        )
        
        self.message_queues[channel].append(message)
        logger.debug(f"Added message to {channel} queue: {user}: {content[:50]}...")
    
    def get_relevant_context(self, channel: str, query: str, max_messages: Optional[int] = None) -> List[Message]:
        """
        Get contextually relevant messages for a given query
        
        Args:
            channel: The channel to get context from
            query: The user's question/request
            max_messages: Maximum number of messages to return (uses config default if None)
        
        Returns:
            List of relevant Message objects, ordered chronologically
        """
        if not self.config.CONTEXT_ANALYSIS_ENABLED:
            return []
        
        if channel not in self.message_queues:
            return []
        
        max_msgs = max_messages or self.config.MAX_CONTEXT_MESSAGES
        messages = list(self.message_queues[channel])
        
        if not messages:
            return []
        
        # Score all messages for relevance
        scored_messages = []
        for msg in messages:
            score = self._calculate_relevance_score(query, msg)
            if score >= self.config.CONTEXT_RELEVANCE_THRESHOLD:
                scored_messages.append((score, msg))
        
        # Sort by relevance score (descending) then by timestamp (ascending for chronological order)
        scored_messages.sort(key=lambda x: (-x[0], x[1].timestamp))
        
        # Return top relevant messages, limited by max_messages
        relevant_messages = [msg for score, msg in scored_messages[:max_msgs]]
        
        # Sort the final result chronologically
        relevant_messages.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Found {len(relevant_messages)} relevant messages out of {len(messages)} total for query: {query[:50]}...")
        
        return relevant_messages
    
    def get_recent_context(self, channel: str, limit: int = 5) -> List[Message]:
        """Get the most recent messages from a channel (simpler context)"""
        if channel not in self.message_queues:
            return []
        
        messages = list(self.message_queues[channel])
        return messages[-limit:] if messages else []
    
    def _calculate_relevance_score(self, query: str, message: Message) -> float:
        """
        Calculate relevance score between a query and a message
        
        Returns:
            Float between 0.0 and 1.0 indicating relevance
        """
        score = 0.0
        query_lower = query.lower()
        content_lower = message.content.lower()
        
        # 1. Direct keyword overlap (weighted heavily)
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        if query_words and content_words:
            overlap = len(query_words.intersection(content_words))
            keyword_score = overlap / len(query_words)
            score += keyword_score * 0.4
        
        # 2. Technical keyword bonus
        query_has_tech = any(keyword in query_lower for keyword in self._technical_keywords)
        content_has_tech = any(keyword in content_lower for keyword in self._technical_keywords)
        
        if query_has_tech and content_has_tech:
            # Find specific technical keywords that match
            matching_tech = [kw for kw in self._technical_keywords 
                           if kw in query_lower and kw in content_lower]
            if matching_tech:
                score += min(0.3, len(matching_tech) * 0.1)
        
        # 3. Question context bonus
        query_is_question = self._is_question(query)
        content_is_question = self._is_question(message.content)
        
        if query_is_question and content_is_question:
            score += 0.15  # Related questions are often relevant
        elif query_is_question and not content_is_question:
            score += 0.1   # Statements can answer questions
        
        # 4. Recency bonus (more recent = slightly more relevant)
        age_minutes = (time.time() - message.timestamp) / 60
        if age_minutes < 30:  # Last 30 minutes
            recency_bonus = max(0, 0.1 * (1 - age_minutes / 30))
            score += recency_bonus
        
        # 5. Bot interaction bonus
        if message.is_bot_mention or message.is_command:
            score += 0.1
        
        # 6. User continuity bonus (same user asking follow-up)
        # This would require tracking the current user, which we'd need to pass in
        # For now, we'll skip this but it could be added later
        
        # 7. Length penalty for very short messages (likely not contextually rich)
        if len(message.content.strip()) < 10:
            score *= 0.7
        
        # 8. URL/link bonus if query is about links or resources
        if any(word in query_lower for word in ['link', 'url', 'resource', 'site', 'website']):
            if any(word in content_lower for word in ['http', 'https', 'www', '.com', '.org', '.net']):
                score += 0.2
        
        return min(1.0, score)  # Cap at 1.0
    
    def _is_question(self, text: str) -> bool:
        """Check if a text appears to be a question"""
        for pattern in self._question_patterns:
            if pattern.search(text):
                return True
        return False
    
    def get_context_summary(self, channel: str) -> Dict:
        """Get summary statistics about the message queue for a channel"""
        if channel not in self.message_queues:
            return {
                'total_messages': 0,
                'unique_users': 0,
                'commands': 0,
                'bot_mentions': 0,
                'oldest_timestamp': None,
                'newest_timestamp': None
            }
        
        messages = list(self.message_queues[channel])
        if not messages:
            return {
                'total_messages': 0,
                'unique_users': 0,
                'commands': 0,
                'bot_mentions': 0,
                'oldest_timestamp': None,
                'newest_timestamp': None
            }
        
        users = set(msg.user for msg in messages)
        commands = sum(1 for msg in messages if msg.is_command)
        mentions = sum(1 for msg in messages if msg.is_bot_mention)
        
        return {
            'total_messages': len(messages),
            'unique_users': len(users),
            'commands': commands,
            'bot_mentions': mentions,
            'oldest_timestamp': messages[0].timestamp,
            'newest_timestamp': messages[-1].timestamp
        }
    
    def clear_channel_context(self, channel: str):
        """Clear the message queue for a specific channel"""
        if channel in self.message_queues:
            self.message_queues[channel].clear()
            logger.info(f"Cleared message context for channel {channel}")
    
    def format_context_for_llm(self, messages: List[Message]) -> str:
        """Format a list of messages for inclusion in LLM context"""
        if not messages:
            return ""
        
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
            
            # Add context indicators
            indicators = []
            if msg.is_command:
                indicators.append("cmd")
            if msg.is_bot_mention:
                indicators.append("@bot")
            
            indicator_str = f" [{','.join(indicators)}]" if indicators else ""
            
            formatted_lines.append(f"[{time_str}] {msg.user}{indicator_str}: {msg.content}")
        
        return "\n".join(formatted_lines)
