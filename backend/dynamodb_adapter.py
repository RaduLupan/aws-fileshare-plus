"""
DynamoDB Adapter - Production database layer for FileShare Plus
"""
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Table names
USERS_TABLE = 'fileshare-users'
URLS_TABLE = 'fileshare-urls'

class DynamoDBAdapter:
    """DynamoDB adapter for user and URL management"""
    
    def __init__(self):
        self.users_table = dynamodb.Table(USERS_TABLE)
        self.urls_table = dynamodb.Table(URLS_TABLE)
    
    # User Management Functions
    def create_or_update_user(self, user_id, email, user_tier='Free'):
        """Create or update user in DynamoDB"""
        try:
            item = {
                'user_id': user_id,
                'email': email,
                'user_tier': user_tier,
                'trial_used': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.users_table.put_item(Item=item)
            logger.info(f"User {user_id} created/updated with tier {user_tier}")
            return True
        except Exception as e:
            logger.error(f"Failed to create/update user {user_id}: {e}")
            return False
    
    def get_user_by_id(self, user_id):
        """Get user information by user_id"""
        try:
            response = self.users_table.get_item(Key={'user_id': user_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user information by email"""
        try:
            response = self.users_table.query(
                IndexName='email-index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    def get_user_trial_status(self, user_email, user_id):
        """Get comprehensive trial status for a user"""
        try:
            # First, try to get user by ID
            user = self.get_user_by_id(user_id)
            
            # If not found, try by email
            if not user:
                user = self.get_user_by_email(user_email)
            
            # If still not found, create new user
            if not user:
                logger.info(f"Creating new user: {user_email}")
                self.create_or_update_user(user_id, user_email, 'Free')
                return {
                    'user_tier': 'Free',
                    'trial_status': 'not_started',
                    'can_start_trial': True,
                    'days_remaining': 0,
                    'trial_started_at': None,
                    'trial_expires_at': None
                }
            
            # Check trial status
            trial_expires_at = user.get('trial_expires_at')
            trial_started_at = user.get('trial_started_at')
            
            if not trial_started_at:
                return {
                    'user_tier': user.get('user_tier', 'Free'),
                    'trial_status': 'not_started',
                    'can_start_trial': not user.get('trial_used', False),
                    'days_remaining': 0,
                    'trial_started_at': None,
                    'trial_expires_at': None
                }
            
            # Check if trial has expired
            if trial_expires_at:
                try:
                    expires_dt = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
                    now = datetime.now()
                    
                    if expires_dt.tzinfo:
                        from datetime import timezone
                        now = now.replace(tzinfo=timezone.utc)
                    
                    if now > expires_dt:
                        return {
                            'user_tier': user.get('user_tier', 'Free'),
                            'trial_status': 'expired',
                            'can_start_trial': False,
                            'days_remaining': 0,
                            'trial_started_at': trial_started_at,
                            'trial_expires_at': trial_expires_at
                        }
                    else:
                        days_remaining = (expires_dt - now).days
                        return {
                            'user_tier': user.get('user_tier', 'Free'),
                            'trial_status': 'active',
                            'can_start_trial': False,
                            'days_remaining': max(0, days_remaining),
                            'trial_started_at': trial_started_at,
                            'trial_expires_at': trial_expires_at
                        }
                except Exception as date_error:
                    logger.error(f"Error parsing trial dates for user {user_email}: {date_error}")
            
            # Fallback
            return {
                'user_tier': user.get('user_tier', 'Free'),
                'trial_status': 'not_started',
                'can_start_trial': not user.get('trial_used', False),
                'days_remaining': 0,
                'trial_started_at': trial_started_at,
                'trial_expires_at': trial_expires_at
            }
            
        except Exception as e:
            logger.error(f"Error getting trial status for user {user_email}: {e}")
            return {
                'user_tier': 'Free',
                'trial_status': 'not_started',
                'can_start_trial': True,
                'days_remaining': 0,
                'trial_started_at': None,
                'trial_expires_at': None
            }
    
    def start_premium_trial(self, user_id, user_email):
        """Start a 30-day Premium trial for a user"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                user = self.get_user_by_email(user_email)
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            if user.get('trial_used'):
                logger.warning(f"User {user_id} has already used their trial")
                return False
            
            # Calculate expiration date
            trial_started = datetime.now()
            trial_expires = trial_started + timedelta(days=30)
            
            # Update user
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET trial_started_at = :start, trial_expires_at = :expires, trial_used = :used, user_tier = :tier, updated_at = :updated',
                ExpressionAttributeValues={
                    ':start': trial_started.isoformat(),
                    ':expires': trial_expires.isoformat(),
                    ':used': True,
                    ':tier': 'Premium-Trial',
                    ':updated': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Premium trial started for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trial for user {user_id}: {e}")
            return False
    
    def expire_trials(self):
        """Expire all trials that have passed their expiration date"""
        try:
            # Scan for expired trials
            response = self.users_table.scan(
                FilterExpression='user_tier = :tier AND trial_expires_at < :now',
                ExpressionAttributeValues={
                    ':tier': 'Premium-Trial',
                    ':now': datetime.now().isoformat()
                }
            )
            
            expired_count = 0
            for user in response['Items']:
                # Update user tier to Free
                self.users_table.update_item(
                    Key={'user_id': user['user_id']},
                    UpdateExpression='SET user_tier = :tier, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':tier': 'Free',
                        ':updated': datetime.now().isoformat()
                    }
                )
                expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Expired {expired_count} Premium trials")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to expire trials: {e}")
            return 0
    
    # URL Management Functions
    def create_url_mapping(self, short_code, full_url, expires_in_days=7, created_by_user=None, file_key=None, filename=None):
        """Create a new URL mapping"""
        try:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            item = {
                'short_code': short_code,
                'full_url': full_url,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'expires_in_days': expires_in_days,
                'click_count': 0
            }
            
            if created_by_user:
                item['created_by_user'] = created_by_user
            if file_key:
                item['file_key'] = file_key
            if filename:
                item['filename'] = filename
            
            self.urls_table.put_item(Item=item)
            logger.info(f"URL mapping created: {short_code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create URL mapping {short_code}: {e}")
            return False
    
    def get_url_mapping(self, short_code):
        """Get URL mapping by short code"""
        try:
            response = self.urls_table.get_item(Key={'short_code': short_code})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get URL mapping {short_code}: {e}")
            return None
    
    def increment_click_count(self, short_code):
        """Increment click count for a URL"""
        try:
            self.urls_table.update_item(
                Key={'short_code': short_code},
                UpdateExpression='ADD click_count :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to increment click count for {short_code}: {e}")
            return False
    
    def cleanup_expired_urls(self):
        """Remove expired URLs"""
        try:
            response = self.urls_table.scan(
                FilterExpression='expires_at < :now',
                ExpressionAttributeValues={':now': datetime.now().isoformat()}
            )
            
            deleted_count = 0
            for url in response['Items']:
                self.urls_table.delete_item(Key={'short_code': url['short_code']})
                deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired URLs")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired URLs: {e}")
            return 0

# Global adapter instance
db_adapter = DynamoDBAdapter()

# Compatibility functions for existing code
def create_or_update_user(user_id, email, user_tier='Free'):
    return db_adapter.create_or_update_user(user_id, email, user_tier)

def get_user_by_id(user_id):
    return db_adapter.get_user_by_id(user_id)

def get_user_by_email(email):
    return db_adapter.get_user_by_email(email)

def start_premium_trial(user_id):
    user = get_user_by_id(user_id)
    if user:
        return db_adapter.start_premium_trial(user_id, user['email'])
    return False

def expire_trials():
    return db_adapter.expire_trials()

def cleanup_expired_urls():
    return db_adapter.cleanup_expired_urls()

@contextmanager
def get_db_connection():
    """Context manager for backward compatibility"""
    yield db_adapter