"""
Database setup and management for URL shortener
"""
import sqlite3
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'url_shortener.db')

def init_database():
    """Initialize the database with required tables"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create url_mappings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS url_mappings (
                    short_code VARCHAR(10) PRIMARY KEY,
                    full_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    click_count INTEGER DEFAULT 0,
                    created_by_user VARCHAR(255),
                    file_key VARCHAR(255),
                    filename VARCHAR(255)
                )
            ''')
            
            # Create index for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_by_user 
                ON url_mappings(created_by_user)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON url_mappings(expires_at)
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def cleanup_expired_urls():
    """Remove expired URLs from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM url_mappings 
                WHERE expires_at IS NOT NULL 
                AND expires_at < CURRENT_TIMESTAMP
            ''')
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired URLs")
                
    except Exception as e:
        logger.error(f"Failed to cleanup expired URLs: {e}")

# Initialize database on import
init_database()
