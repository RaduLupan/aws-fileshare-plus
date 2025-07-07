"""
URL Shortener core functionality
"""
import string
import random
import hashlib
from datetime import datetime, timedelta
from database import get_db_connection, cleanup_expired_urls
import logging

logger = logging.getLogger(__name__)

# Characters for base62 encoding (0-9, a-z, A-Z)
BASE62_CHARS = string.digits + string.ascii_lowercase + string.ascii_uppercase

def generate_short_code(length=6):
    """Generate a random short code using base62 encoding"""
    return ''.join(random.choice(BASE62_CHARS) for _ in range(length))

def generate_deterministic_code(full_url, length=8):
    """Generate a deterministic short code based on URL hash"""
    # Create hash of the URL
    hash_object = hashlib.md5(full_url.encode())
    hash_hex = hash_object.hexdigest()
    
    # Convert hex to base62
    hash_int = int(hash_hex[:16], 16)  # Use first 16 chars of hex
    
    if hash_int == 0:
        return generate_short_code(length)
    
    code = ""
    while hash_int > 0 and len(code) < length:
        code = BASE62_CHARS[hash_int % 62] + code
        hash_int //= 62
    
    # Pad with random chars if needed
    while len(code) < length:
        code = random.choice(BASE62_CHARS) + code
    
    return code[:length]

def create_short_url(full_url, user_email=None, file_key=None, filename=None, expires_in_days=7):
    """
    Create a short URL mapping
    
    Args:
        full_url: The full URL to shorten
        user_email: Email of the user creating the URL
        file_key: S3 file key (optional)
        filename: Original filename (optional)
        expires_in_days: Expiration in days (default 7)
    
    Returns:
        dict with short_code and created status
    """
    cleanup_expired_urls()  # Clean up old URLs first
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if URL already exists for this user
            cursor.execute('''
                SELECT short_code FROM url_mappings 
                WHERE full_url = ? AND created_by_user = ?
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                LIMIT 1
            ''', (full_url, user_email))
            
            existing = cursor.fetchone()
            if existing:
                logger.info(f"Returning existing short code for URL: {existing['short_code']}")
                return {
                    'short_code': existing['short_code'],
                    'created': False,
                    'message': 'URL already shortened'
                }
            
            # Generate new short code
            max_attempts = 10
            for attempt in range(max_attempts):
                short_code = generate_short_code()
                
                # Check if code already exists
                cursor.execute('SELECT 1 FROM url_mappings WHERE short_code = ?', (short_code,))
                if not cursor.fetchone():
                    break
                    
                if attempt == max_attempts - 1:
                    raise Exception("Failed to generate unique short code")
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Insert new mapping
            cursor.execute('''
                INSERT INTO url_mappings 
                (short_code, full_url, created_by_user, file_key, filename, expires_at, expires_in_days)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (short_code, full_url, user_email, file_key, filename, expires_at, expires_in_days))
            
            conn.commit()
            
            logger.info(f"Created short URL: {short_code} for user: {user_email}")
            
            return {
                'short_code': short_code,
                'created': True,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'message': 'Short URL created successfully'
            }
            
    except Exception as e:
        logger.error(f"Failed to create short URL: {e}")
        raise

def get_full_url(short_code):
    """
    Retrieve full URL by short code and increment click count
    
    Args:
        short_code: The short code to look up
        
    Returns:
        dict with full_url and metadata, or None if not found
    """
    cleanup_expired_urls()  # Clean up old URLs first
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get URL and check expiration
            cursor.execute('''
                SELECT full_url, created_by_user, file_key, filename, 
                       expires_at, expires_in_days, click_count, created_at
                FROM url_mappings 
                WHERE short_code = ?
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', (short_code,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Increment click count
            cursor.execute('''
                UPDATE url_mappings 
                SET click_count = click_count + 1 
                WHERE short_code = ?
            ''', (short_code,))
            
            conn.commit()
            
            return {
                'full_url': row['full_url'],
                'created_by_user': row['created_by_user'],
                'file_key': row['file_key'],
                'filename': row['filename'],
                'expires_at': row['expires_at'],
                'expires_in_days': row['expires_in_days'],
                'click_count': row['click_count'] + 1,  # Return updated count
                'created_at': row['created_at']
            }
            
    except Exception as e:
        logger.error(f"Failed to get full URL for {short_code}: {e}")
        return None

def get_user_urls(user_email, limit=100):
    """
    Get all URLs created by a user
    
    Args:
        user_email: User's email address
        limit: Maximum number of URLs to return
        
    Returns:
        List of URL mappings
    """
    cleanup_expired_urls()  # Clean up old URLs first
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT short_code, full_url, file_key, filename, 
                       click_count, created_at, expires_at, expires_in_days
                FROM url_mappings 
                WHERE created_by_user = ?
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_email, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Failed to get URLs for user {user_email}: {e}")
        return []

def delete_short_url(short_code, user_email):
    """
    Delete a short URL (only if created by the user)
    
    Args:
        short_code: The short code to delete
        user_email: User's email (for authorization)
        
    Returns:
        bool: True if deleted, False if not found or unauthorized
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Delete only if user owns the URL
            cursor.execute('''
                DELETE FROM url_mappings 
                WHERE short_code = ? AND created_by_user = ?
            ''', (short_code, user_email))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"Deleted short URL {short_code} for user {user_email}")
            
            return deleted
            
    except Exception as e:
        logger.error(f"Failed to delete short URL {short_code}: {e}")
        return False
