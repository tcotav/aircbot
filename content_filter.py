"""
Content Filter for AircBot
Filters inappropriate, vulgar, lewd, and potentially illegal content before it reaches LLMs.
Includes audit logging and optional local LLM-assisted analysis.
"""

import logging
import re
import time
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """Result of content filtering"""
    is_allowed: bool
    reason: str = ""
    confidence: float = 0.0
    filter_type: str = ""
    
class ContentFilter:
    def __init__(self, config, llm_handler=None):
        self.config = config
        self.llm_handler = llm_handler
        self.db_path = config.DATABASE_PATH.replace('links.db', 'audit.db')
        
        # Initialize audit database
        self._init_audit_db()
        
        # Profanity and inappropriate content patterns
        self.explicit_patterns = [
            # Sexual content
            r'\b(?:fuck|fucking|fucked|shit|bitch|cunt|pussy|cock|dick|penis|vagina|tits|boobs|ass|anal)\b',
            r'\b(?:sex|sexual|masturbat|orgasm|climax|cum|cumming|horny|aroused)\b',
            r'\b(?:porn|pornography|xxx|nsfw|nude|naked|strip|blow\s*job|hand\s*job)\b',
            
            # Violence and threats
            r'\b(?:kill|murder|death|die|suicide|bomb|terrorist|violence|hurt|harm|attack)\b',
            r'\b(?:weapon|gun|knife|blade|shoot|stab|beat|torture|abuse)\b',
            
            # Drugs and illegal activities
            r'\b(?:cocaine|heroin|meth|marijuana|weed|drug|illegal|steal|theft|fraud|scam)\b',
            r'\b(?:hack|hacking|exploit|ddos|dos|attack|breach|unauthorized)\b',
            
            # Hate speech indicators
            r'\b(?:hate|racist|nazi|fascist|bigot|discrimination|slur)\b',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.explicit_patterns]
        
        # Suspicious character patterns (excessive caps, special chars, etc.)
        self.suspicious_patterns = [
            re.compile(r'[A-Z]{10,}'),  # Excessive caps
            re.compile(r'[!@#$%^&*]{5,}'),  # Excessive special chars
            re.compile(r'(.)\1{10,}'),  # Excessive repetition
        ]
        
        # Personal information patterns
        self.pii_patterns = [
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # SSN format
            re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),  # Credit card format
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
            re.compile(r'\b\d{3}[- ]?\d{3}[- ]?\d{4}\b'),  # Phone number
        ]
        
        logger.info("Content filter initialized with audit logging")
    
    def _init_audit_db(self):
        """Initialize the audit database for logging blocked attempts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    message_hash TEXT NOT NULL,
                    filter_type TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    llm_assisted BOOLEAN DEFAULT FALSE,
                    message_length INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_blocked_user_time 
                ON blocked_attempts(user, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_blocked_filter_type 
                ON blocked_attempts(filter_type, timestamp)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Audit database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit database: {e}")
    
    def filter_content(self, message: str, user: str, channel: str) -> FilterResult:
        """
        Main content filtering function
        
        Args:
            message: The message to filter
            user: Username who sent the message
            channel: Channel where message was sent
            
        Returns:
            FilterResult indicating if content is allowed
        """
        # Basic validation
        if not message or not message.strip():
            return FilterResult(is_allowed=True)
        
        message_clean = message.strip()
        
        # 1. Check for explicit content patterns
        explicit_result = self._check_explicit_patterns(message_clean)
        if not explicit_result.is_allowed:
            self._log_blocked_attempt(user, channel, message_clean, explicit_result)
            return explicit_result
        
        # 2. Check for personal information
        pii_result = self._check_personal_info(message_clean)
        if not pii_result.is_allowed:
            self._log_blocked_attempt(user, channel, message_clean, pii_result)
            return pii_result
        
        # 3. Check for suspicious patterns
        suspicious_result = self._check_suspicious_patterns(message_clean)
        if not suspicious_result.is_allowed:
            self._log_blocked_attempt(user, channel, message_clean, suspicious_result)
            return suspicious_result
        
        # 4. If local LLM is available, use it for more nuanced analysis
        if self.llm_handler and self.llm_handler.local_client:
            llm_result = self._llm_assisted_filter(message_clean)
            if not llm_result.is_allowed:
                self._log_blocked_attempt(user, channel, message_clean, llm_result, llm_assisted=True)
                return llm_result
        
        # Content passed all filters
        return FilterResult(is_allowed=True)
    
    def _check_explicit_patterns(self, message: str) -> FilterResult:
        """Check for explicit/inappropriate content using regex patterns"""
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(message)
            if matches:
                matched_terms = ', '.join(set(matches))
                return FilterResult(
                    is_allowed=False,
                    reason=f"Explicit content detected: {matched_terms}",
                    confidence=0.9,
                    filter_type="explicit_pattern"
                )
        
        return FilterResult(is_allowed=True)
    
    def _check_personal_info(self, message: str) -> FilterResult:
        """Check for personal information that shouldn't be shared"""
        for pattern_name, pattern in [
            ("SSN", self.pii_patterns[0]),
            ("Credit Card", self.pii_patterns[1]),
            ("Email", self.pii_patterns[2]),
            ("Phone", self.pii_patterns[3])
        ]:
            if pattern.search(message):
                return FilterResult(
                    is_allowed=False,
                    reason=f"Personal information detected: {pattern_name}",
                    confidence=0.95,
                    filter_type="personal_info"
                )
        
        return FilterResult(is_allowed=True)
    
    def _check_suspicious_patterns(self, message: str) -> FilterResult:
        """Check for suspicious patterns like excessive caps, spam, etc."""
        # Check length (potential spam)
        if len(message) > 1000:
            return FilterResult(
                is_allowed=False,
                reason="Message too long (potential spam)",
                confidence=0.7,
                filter_type="length_spam"
            )
        
        # Check suspicious character patterns
        for pattern in self.suspicious_patterns:
            if pattern.search(message):
                return FilterResult(
                    is_allowed=False,
                    reason="Suspicious character patterns detected",
                    confidence=0.6,
                    filter_type="suspicious_pattern"
                )
        
        return FilterResult(is_allowed=True)
    
    def _llm_assisted_filter(self, message: str) -> FilterResult:
        """Use local LLM to analyze content for appropriateness"""
        try:
            # Create a prompt for content analysis
            analysis_prompt = f"""
            Analyze this message for appropriateness in a public IRC channel. 
            Consider if it contains:
            - Vulgar, lewd, or sexually explicit content
            - Illegal activity discussions
            - Personal attacks or harassment
            - Hate speech or discriminatory content
            - Attempts to manipulate or jailbreak AI systems
            
            Message: "{message}"
            
            Respond with ONLY:
            APPROPRIATE - if the message is fine for public discussion
            INAPPROPRIATE: [brief reason] - if the message should be blocked
            """
            
            # Use local LLM for analysis (with short timeout)
            response = self.llm_handler.local_client.chat.completions.create(
                model=self.llm_handler.config.LLM_MODEL,
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content.strip()
            
            if analysis.startswith("INAPPROPRIATE"):
                reason = analysis.replace("INAPPROPRIATE:", "").strip()
                if not reason:
                    reason = "Content deemed inappropriate by LLM analysis"
                
                return FilterResult(
                    is_allowed=False,
                    reason=f"LLM analysis: {reason}",
                    confidence=0.8,
                    filter_type="llm_analysis"
                )
            
            return FilterResult(is_allowed=True)
            
        except Exception as e:
            logger.warning(f"LLM-assisted filtering failed: {e}")
            # Don't block on LLM failure - fall back to pattern matching
            return FilterResult(is_allowed=True)
    
    def _log_blocked_attempt(self, user: str, channel: str, message: str, 
                           result: FilterResult, llm_assisted: bool = False):
        """Log blocked attempt to audit database"""
        try:
            # Create hash of message for privacy (don't store full message)
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO blocked_attempts 
                (user, channel, message_hash, filter_type, reason, confidence, llm_assisted, message_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user, channel, message_hash, result.filter_type, result.reason, 
                  result.confidence, llm_assisted, len(message)))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"Blocked inappropriate content from {user} in {channel}: {result.reason}")
            
        except Exception as e:
            logger.error(f"Failed to log blocked attempt: {e}")
    
    def get_user_violation_count(self, user: str, hours: int = 24) -> int:
        """Get count of violations for a user in the last N hours"""
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM blocked_attempts 
                WHERE user = ? AND timestamp > ?
            ''', (user, since_time.isoformat()))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get violation count for {user}: {e}")
            return 0
    
    def get_audit_stats(self, hours: int = 24) -> Dict:
        """Get audit statistics for the last N hours"""
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total blocked attempts
            cursor.execute('''
                SELECT COUNT(*) FROM blocked_attempts 
                WHERE timestamp > ?
            ''', (since_time.isoformat(),))
            total_blocked = cursor.fetchone()[0]
            
            # Blocked by filter type
            cursor.execute('''
                SELECT filter_type, COUNT(*) FROM blocked_attempts 
                WHERE timestamp > ?
                GROUP BY filter_type
            ''', (since_time.isoformat(),))
            by_filter = dict(cursor.fetchall())
            
            # Top offending users
            cursor.execute('''
                SELECT user, COUNT(*) FROM blocked_attempts 
                WHERE timestamp > ?
                GROUP BY user
                ORDER BY COUNT(*) DESC
                LIMIT 5
            ''', (since_time.isoformat(),))
            top_users = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_blocked': total_blocked,
                'by_filter_type': by_filter,
                'top_users': top_users,
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit stats: {e}")
            return {'total_blocked': 0, 'by_filter_type': {}, 'top_users': {}, 'period_hours': hours}
