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
        logger.info(f"Initializing database at {DB_PATH}")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create users table for trial tracking
            logger.info("Creating users table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(255) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    user_tier VARCHAR(20) DEFAULT 'Free',
                    trial_started_at TIMESTAMP,
                    trial_expires_at TIMESTAMP,
                    trial_used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Users table created successfully")
            
            # Create url_mappings table
            logger.info("Creating url_mappings table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS url_mappings (
                    short_code VARCHAR(10) PRIMARY KEY,
                    full_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    expires_in_days INTEGER DEFAULT 7,
                    click_count INTEGER DEFAULT 0,
                    created_by_user VARCHAR(255),
                    file_key VARCHAR(255),
                    filename VARCHAR(255),
                    FOREIGN KEY (created_by_user) REFERENCES users(user_id)
                )
            ''')
            logger.info("URL mappings table created successfully")
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_tier 
                ON users(user_tier)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_trial_expires 
                ON users(trial_expires_at)
            ''')
            
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
            
            # Run migrations
            migrate_database(conn)
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def migrate_database(conn):
    """Handle database migrations for schema changes"""
    try:
        cursor = conn.cursor()
        
        # Check if expires_in_days column exists in url_mappings
        cursor.execute("PRAGMA table_info(url_mappings)")
        url_columns = [column[1] for column in cursor.fetchall()]
        
        if 'expires_in_days' not in url_columns:
            logger.info("Adding expires_in_days column to url_mappings table")
            cursor.execute('ALTER TABLE url_mappings ADD COLUMN expires_in_days INTEGER DEFAULT 7')
            
            # Update existing records to have default 7-day expiration
            cursor.execute('UPDATE url_mappings SET expires_in_days = 7 WHERE expires_in_days IS NULL')
            
            conn.commit()
            logger.info("Migration completed: expires_in_days column added")
        
        # Check if users table exists and has trial columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table_exists = cursor.fetchone() is not None
        
        if users_table_exists:
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in cursor.fetchall()]
            
            # Add trial columns if they don't exist
            if 'trial_started_at' not in user_columns:
                logger.info("Adding trial tracking columns to users table")
                cursor.execute('ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP')
                cursor.execute('ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP')
                cursor.execute('ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT FALSE')
                conn.commit()
                logger.info("Migration completed: trial tracking columns added")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
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

# User management functions for Premium Trial system
def create_or_update_user(user_id, email, user_tier='Free'):
    """Create or update user in database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, email, user_tier, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, email, user_tier))
            conn.commit()
            logger.info(f"User {user_id} created/updated with tier {user_tier}")
            return True
    except Exception as e:
        logger.error(f"Failed to create/update user {user_id}: {e}")
        return False

def get_user_by_id(user_id):
    """Get user information by user_id"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None

def get_user_by_email(email):
    """Get user information by email"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        logger.error(f"Failed to get user by email {email}: {e}")
        return None

def start_premium_trial(user_id):
    """Start a 30-day Premium trial for a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if user has already used their trial
            cursor.execute('SELECT trial_used FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            if user['trial_used']:
                logger.warning(f"User {user_id} has already used their trial")
                return False
            
            # Start the trial
            cursor.execute('''
                UPDATE users 
                SET trial_started_at = CURRENT_TIMESTAMP,
                    trial_expires_at = datetime(CURRENT_TIMESTAMP, '+30 days'),
                    trial_used = TRUE,
                    user_tier = 'Premium-Trial',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            logger.info(f"Premium trial started for user {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to start trial for user {user_id}: {e}")
        return False

def check_trial_status(user_id):
    """Check if a user's trial is active, expired, or not started"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT trial_started_at, trial_expires_at, trial_used, user_tier
                FROM users WHERE user_id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {'status': 'user_not_found'}
            
            user_dict = dict(user)
            
            # No trial started
            if not user_dict['trial_started_at']:
                return {
                    'status': 'no_trial',
                    'can_start_trial': not user_dict['trial_used'],
                    'user_tier': user_dict['user_tier']
                }
            
            # Check if trial has expired
            cursor.execute('''
                SELECT datetime('now') > trial_expires_at as is_expired
                FROM users WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            
            if result['is_expired']:
                return {
                    'status': 'expired',
                    'trial_started_at': user_dict['trial_started_at'],
                    'trial_expires_at': user_dict['trial_expires_at'],
                    'user_tier': user_dict['user_tier']
                }
            else:
                # Calculate days remaining
                cursor.execute('''
                    SELECT CAST((julianday(trial_expires_at) - julianday('now')) AS INTEGER) as days_remaining
                    FROM users WHERE user_id = ?
                ''', (user_id,))
                days_result = cursor.fetchone()
                
                return {
                    'status': 'active',
                    'trial_started_at': user_dict['trial_started_at'],
                    'trial_expires_at': user_dict['trial_expires_at'],
                    'days_remaining': days_result['days_remaining'],
                    'user_tier': user_dict['user_tier']
                }
                
    except Exception as e:
        logger.error(f"Failed to check trial status for user {user_id}: {e}")
        return {'status': 'error', 'error': str(e)}

def expire_trials():
    """Expire all trials that have passed their expiration date"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET user_tier = 'Free',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_tier = 'Premium-Trial'
                AND trial_expires_at < CURRENT_TIMESTAMP
            ''')
            expired_count = cursor.rowcount
            conn.commit()
            
            if expired_count > 0:
                logger.info(f"Expired {expired_count} Premium trials")
            
            return expired_count
            
    except Exception as e:
        logger.error(f"Failed to expire trials: {e}")
        return 0

def get_users_with_expiring_trials(days_ahead=3):
    """Get users whose trials will expire within the specified number of days"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, email, trial_expires_at,
                       CAST((julianday(trial_expires_at) - julianday('now')) AS INTEGER) as days_remaining
                FROM users 
                WHERE user_tier = 'Premium-Trial'
                AND trial_expires_at > CURRENT_TIMESTAMP
                AND trial_expires_at <= datetime('now', '+{} days')
                ORDER BY trial_expires_at ASC
            '''.format(days_ahead))
            
            users = cursor.fetchall()
            return [dict(user) for user in users]
            
    except Exception as e:
        logger.error(f"Failed to get users with expiring trials: {e}")
        return []

# Initialize database on import
init_database()
