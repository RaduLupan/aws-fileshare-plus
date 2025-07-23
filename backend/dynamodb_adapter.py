"""
DynamoDB Adapter for AWS FileShare Plus
Provides database operations for user management and trial system
"""

import boto3
import os
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamoDBAdapter:
    def __init__(self):
        """Initialize DynamoDB adapter with table names from environment"""
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
        
        # Get table names from environment
        project_name = os.getenv('PROJECT_NAME', 'aws-fileshare-plus')
        environment = os.getenv('ENVIRONMENT', 'prod')
        
        self.users_table_name = os.getenv('DYNAMODB_USERS_TABLE', f"{project_name}-{environment}-users")
        self.short_urls_table_name = os.getenv('DYNAMODB_SHORT_URLS_TABLE', f"{project_name}-{environment}-short-urls")
        
        # Initialize table references
        self.users_table = self.dynamodb.Table(self.users_table_name)
        self.short_urls_table = self.dynamodb.Table(self.short_urls_table_name)
        
        logger.info(f"DynamoDB adapter initialized with tables: {self.users_table_name}, {self.short_urls_table_name}")

    def get_user_trial_status(self, user_email, user_id):
        """Get comprehensive trial status for a user"""
        try:
            # Try to get user by user_id first
            response = self.users_table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' in response:
                user = response['Item']
            else:
                # Try to get user by email using GSI
                response = self.users_table.query(
                    IndexName='email-index',
                    KeyConditionExpression='email = :email',
                    ExpressionAttributeValues={':email': user_email}
                )
                
                if response['Items']:
                    user = response['Items'][0]
                else:
                    # User doesn't exist, create them as a new free tier user
                    user = self._create_new_user(user_id, user_email)
            
            return self._format_trial_status(user)
            
        except Exception as e:
            logger.error(f"Error getting trial status for user {user_email}: {e}")
            # Return default status for new user
            return {
                'user_tier': 'Free',
                'trial_status': 'not_started',
                'can_start_trial': True,
                'days_remaining': 0,
                'trial_started_at': None,
                'trial_expires_at': None
            }

    def _create_new_user(self, user_id, user_email):
        """Create a new user in DynamoDB"""
        try:
            new_user = {
                'user_id': user_id,
                'email': user_email,
                'user_tier': 'Free',
                'trial_used': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.users_table.put_item(Item=new_user)
            logger.info(f"Created new user: {user_email}")
            return new_user
            
        except Exception as e:
            logger.error(f"Error creating new user {user_email}: {e}")
            # Return a default user object
            return {
                'user_id': user_id,
                'email': user_email,
                'user_tier': 'Free',
                'trial_used': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

    def _format_trial_status(self, user):
        """Format user data into trial status response"""
        trial_started_at = user.get('trial_started_at')
        trial_expires_at = user.get('trial_expires_at')
        trial_used = user.get('trial_used', False)
        
        # If trial was never started
        if not trial_started_at:
            return {
                'user_tier': user.get('user_tier', 'Free'),
                'trial_status': 'not_started',
                'can_start_trial': not trial_used,
                'days_remaining': 0,
                'trial_started_at': None,
                'trial_expires_at': None
            }
        
        # Check if trial has expired
        if trial_expires_at:
            try:
                if isinstance(trial_expires_at, str):
                    expires_dt = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
                else:
                    expires_dt = trial_expires_at
                
                now = datetime.now()
                if expires_dt.tzinfo:
                    from datetime import timezone
                    now = now.replace(tzinfo=timezone.utc)
                
                if now > expires_dt:
                    # Trial has expired
                    return {
                        'user_tier': user.get('user_tier', 'Free'),
                        'trial_status': 'expired',
                        'can_start_trial': False,
                        'days_remaining': 0,
                        'trial_started_at': trial_started_at,
                        'trial_expires_at': trial_expires_at
                    }
                else:
                    # Trial is still active
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
                logger.error(f"Error parsing trial dates: {date_error}")
        
        # Fallback - trial status unclear
        return {
            'user_tier': user.get('user_tier', 'Free'),
            'trial_status': 'unknown',
            'can_start_trial': not trial_used,
            'days_remaining': 0,
            'trial_started_at': trial_started_at,
            'trial_expires_at': trial_expires_at
        }

    def start_premium_trial(self, user_id, user_email):
        """Start a 30-day Premium trial for a user"""
        try:
            # Check if user exists
            response = self.users_table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                user = response['Item']
            else:
                # Create new user
                user = self._create_new_user(user_id, user_email)
            
            # Check if trial is already used
            if user.get('trial_used', False):
                logger.warning(f"User {user_email} already used trial")
                return False
            
            # Check if trial is currently active
            trial_expires_at = user.get('trial_expires_at')
            if trial_expires_at:
                try:
                    if isinstance(trial_expires_at, str):
                        expires_dt = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
                    else:
                        expires_dt = trial_expires_at
                    
                    now = datetime.now()
                    if expires_dt.tzinfo:
                        from datetime import timezone
                        now = now.replace(tzinfo=timezone.utc)
                    
                    if now <= expires_dt:
                        logger.warning(f"User {user_email} has active trial")
                        return False
                except Exception as date_error:
                    logger.error(f"Error checking trial expiration: {date_error}")
            
            # Start the trial
            trial_started_at = datetime.utcnow()
            trial_expires_at = trial_started_at + timedelta(days=30)
            
            update_expression = """
                SET user_tier = :tier,
                    trial_used = :trial_used,
                    trial_started_at = :trial_started_at,
                    trial_expires_at = :trial_expires_at,
                    updated_at = :updated_at
            """
            
            expression_values = {
                ':tier': 'Premium',
                ':trial_used': True,
                ':trial_started_at': trial_started_at.isoformat(),
                ':trial_expires_at': trial_expires_at.isoformat(),
                ':updated_at': datetime.utcnow().isoformat()
            }
            
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"Started Premium trial for user {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting trial for user {user_email}: {e}")
            return False

    def expire_trials(self):
        """Process and expire trials that have passed their expiration date"""
        try:
            now = datetime.utcnow()
            expired_count = 0
            
            # Scan all users
            response = self.users_table.scan()
            
            for user in response['Items']:
                trial_expires_at = user.get('trial_expires_at')
                if trial_expires_at and user.get('user_tier') == 'Premium':
                    try:
                        if isinstance(trial_expires_at, str):
                            expires_dt = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
                        else:
                            expires_dt = trial_expires_at
                        
                        if expires_dt.tzinfo:
                            from datetime import timezone
                            now_tz = now.replace(tzinfo=timezone.utc)
                        else:
                            now_tz = now
                        
                        if now_tz > expires_dt:
                            # Expire the trial
                            update_expression = """
                                SET user_tier = :tier,
                                    updated_at = :updated_at
                            """
                            
                            expression_values = {
                                ':tier': 'Free',
                                ':updated_at': now.isoformat()
                            }
                            
                            self.users_table.update_item(
                                Key={'user_id': user['user_id']},
                                UpdateExpression=update_expression,
                                ExpressionAttributeValues=expression_values
                            )
                            
                            expired_count += 1
                            logger.info(f"Expired trial for user {user.get('email', 'unknown')}")
                            
                    except Exception as date_error:
                        logger.error(f"Error processing trial expiration for user {user.get('email', 'unknown')}: {date_error}")
            
            logger.info(f"Processed {expired_count} expired trials")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error processing expired trials: {e}")
            return 0

    def get_user_info(self, user_email, user_id):
        """Get user information"""
        try:
            # Try to get user by user_id first
            response = self.users_table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return response['Item']
            
            # Try to get user by email using GSI
            response = self.users_table.query(
                IndexName='email-index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': user_email}
            )
            
            if response['Items']:
                return response['Items'][0]
            
            # User doesn't exist, create them
            return self._create_new_user(user_id, user_email)
            
        except Exception as e:
            logger.error(f"Error getting user info for {user_email}: {e}")
            return None

    def initialize_user(self, user_email, user_id):
        """Initialize a new user in the system"""
        try:
            # Check if user already exists
            existing_user = self.get_user_info(user_email, user_id)
            if existing_user:
                return existing_user
            
            # Create new user
            return self._create_new_user(user_id, user_email)
            
        except Exception as e:
            logger.error(f"Error initializing user {user_email}: {e}")
            return None

# Create a global instance
db_adapter = DynamoDBAdapter() 