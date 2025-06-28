import logging
import time
from datetime import datetime, timedelta
import sqlite3
import os

logger = logging.getLogger(__name__)

class OpenAIRateLimiter:
    """Rate limiter specifically for OpenAI API calls with daily limits"""
    
    def __init__(self, config):
        self.config = config
        self.daily_limit = config.OPENAI_DAILY_LIMIT
        self.db_path = config.DATABASE_PATH
        
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize the database table for tracking OpenAI usage
        self._init_database()
        
        logger.info(f"OpenAI rate limiter initialized: {self.daily_limit} calls per day")
    
    def _init_database(self):
        """Initialize the database table for tracking OpenAI API usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS openai_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        call_count INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(date)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI usage database: {e}")
    
    def _get_today_date(self):
        """Get today's date as a string"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_today_usage(self):
        """Get today's OpenAI usage count"""
        today = self._get_today_date()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT call_count FROM openai_usage WHERE date = ?',
                    (today,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Failed to get today's OpenAI usage: {e}")
            return 0
    
    def _increment_usage(self):
        """Increment today's usage count"""
        today = self._get_today_date()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use INSERT OR REPLACE to handle both new days and existing days
                conn.execute('''
                    INSERT OR REPLACE INTO openai_usage (date, call_count)
                    VALUES (?, COALESCE((SELECT call_count FROM openai_usage WHERE date = ?), 0) + 1)
                ''', (today, today))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to increment OpenAI usage: {e}")
    
    def can_make_request(self):
        """Check if we can make an OpenAI request without exceeding daily limit"""
        if self.daily_limit <= 0:  # 0 or negative means unlimited
            return True
            
        current_usage = self._get_today_usage()
        return current_usage < self.daily_limit
    
    def record_request(self):
        """Record that an OpenAI request was made"""
        self._increment_usage()
        logger.debug(f"OpenAI request recorded. Today's usage: {self._get_today_usage()}/{self.daily_limit}")
    
    def get_usage_stats(self):
        """Get current usage statistics"""
        today_usage = self._get_today_usage()
        remaining = max(0, self.daily_limit - today_usage) if self.daily_limit > 0 else "unlimited"
        
        return {
            'today_usage': today_usage,
            'daily_limit': self.daily_limit,
            'remaining': remaining,
            'date': self._get_today_date()
        }
    
    def cleanup_old_records(self, days_to_keep=30):
        """Clean up old usage records to prevent database growth"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('DELETE FROM openai_usage WHERE date < ?', (cutoff_date,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old OpenAI usage records")
        except Exception as e:
            logger.error(f"Failed to cleanup old OpenAI usage records: {e}")
