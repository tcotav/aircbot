import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create directory if there's a directory component
            os.makedirs(db_dir, exist_ok=True)
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
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO links (url, title, description, user, channel)
                    VALUES (?, ?, ?, ?, ?)
                ''', (url, title, description, user, channel))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Link already exists in this channel
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
                ORDER BY timestamp DESC
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
