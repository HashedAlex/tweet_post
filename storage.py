"""SQLite storage for tracking posted news and preventing duplicates."""

import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict


class NewsStorage:
    def __init__(self, db_path: str = "news_history.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posted_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                posted_at TIMESTAMP NOT NULL,
                tweet_text TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_news_hash(self, title: str, source: str) -> str:
        """Generate a unique hash for a news article."""
        content = f"{title}|{source}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_already_posted(self, title: str, source: str) -> bool:
        """Check if a news article has already been posted."""
        news_hash = self.get_news_hash(title, source)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM posted_news WHERE news_hash = ?",
            (news_hash,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def mark_as_posted(self, title: str, source: str, tweet_text: str):
        """Mark a news article as posted."""
        news_hash = self.get_news_hash(title, source)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO posted_news (news_hash, title, source, posted_at, tweet_text)
                   VALUES (?, ?, ?, ?, ?)""",
                (news_hash, title, source, datetime.now(), tweet_text)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Already posted, ignore
            pass
        finally:
            conn.close()
    
    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Get recent posted news for debugging."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT title, source, posted_at, tweet_text 
               FROM posted_news 
               ORDER BY posted_at DESC 
               LIMIT ?""",
            (limit,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "title": row[0],
                "source": row[1],
                "posted_at": row[2],
                "tweet_text": row[3]
            }
            for row in rows
        ]
