import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create directory if there's a directory component
            try:
                os.makedirs(db_dir, exist_ok=True)
            except (OSError, PermissionError) as e:
                logger.error(f"Cannot create database directory {db_dir}: {e}")
                raise
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    user TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url, channel)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_link(self, url: str, title: str, description: str, user: str, channel: str) -> bool:
        """Save a link to the database. Returns True if saved, False if duplicate"""
        # Add validation for empty URLs
        if not url or not url.strip():
            logger.error("Cannot save link: URL is empty")
            return False
            
        try:
            # Truncate very long content to prevent issues
            if title and len(title) > 500:
                title = title[:497] + "..."
            if description and len(description) > 2000:
                description = description[:1997] + "..."
                
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO links (url, title, description, user, channel, timestamp)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (url, title or '', description or '', user, channel))
                conn.commit()
                return True
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.info(f"Link already exists: {url}")
                return False
            else:
                logger.error(f"Database integrity error saving link: {e}")
                return False
        except Exception as e:
            logger.error(f"Error saving link {url}: {e}")
            return False
    
    def save_message(self, user: str, channel: str, message: str):
        """Save a message to the database for context/memory"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO messages (user, channel, message)
                VALUES (?, ?, ?)
            ''', (user, channel, message))
            conn.commit()
    
    def get_recent_links(self, channel: str, limit: int = 10) -> List[Dict]:
        """Get recent links from a channel"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, title, user, timestamp
                FROM links
                WHERE channel = ?
                ORDER BY timestamp DESC, rowid DESC
                LIMIT ?
            ''', (channel, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_links(self, channel: str, query: str, limit: int = 10) -> List[Dict]:
        """Search links by title or URL"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, title, user, timestamp
                FROM links
                WHERE channel = ? AND (title LIKE ? OR url LIKE ?)
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (channel, f'%{query}%', f'%{query}%', limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_link_stats(self, channel: str) -> Dict:
        """Get basic statistics about saved links"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT COUNT(*) as total_links,
                       COUNT(DISTINCT user) as unique_users
                FROM links
                WHERE channel = ?
            ''', (channel,))
            
            stats = dict(cursor.fetchone())
            
            # Get top contributor
            cursor = conn.execute('''
                SELECT user, COUNT(*) as count
                FROM links
                WHERE channel = ?
                GROUP BY user
                ORDER BY count DESC
                LIMIT 1
            ''', (channel,))
            
            top_user = cursor.fetchone()
            if top_user:
                stats['top_contributor'] = top_user['user']
                stats['top_contributor_count'] = top_user['count']
            
            return stats
        
    def get_links_with_details(self, channel: str, limit: int = 10) -> List[Dict]:
        """Get recent links with formatted timestamps and all details"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, title, description, user, channel, 
                       datetime(timestamp, 'localtime') as formatted_time,
                       timestamp
                FROM links
                WHERE channel = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (channel, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_links_by_user(self, channel: str, user: str) -> List[Dict]:
        """Get all links shared by a specific user in a channel"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, title, user, datetime(timestamp, 'localtime') as formatted_time
                FROM links
                WHERE channel = ? AND user = ?
                ORDER BY timestamp DESC
            ''', (channel, user))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_links_by_user(self, channel: str, user: str, limit: int = 50) -> List[Dict]:
        """Get links by specific user - alias for get_all_links_by_user with limit"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT url, title, user, timestamp
                FROM links
                WHERE channel = ? AND user = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (channel, user, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self, channel: str) -> Dict:
        """Get statistics for a channel - alias for get_link_stats"""
        stats = self.get_link_stats(channel)
        
        # Add top contributors list
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT user, COUNT(*) as count
                FROM links
                WHERE channel = ?
                GROUP BY user
                ORDER BY count DESC
                LIMIT 5
            ''', (channel,))
            
            contributors = [dict(row) for row in cursor.fetchall()]
            stats['top_contributors'] = {row['user']: row['count'] for row in contributors}
            
        return stats
