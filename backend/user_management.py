"""
User management functions for Premium Trial system
"""
import logging
from datetime import datetime, timedelta
from database import (
    create_or_update_user, 
    get_user_by_id, 
    get_user_by_email,
    start_premium_trial,
    check_trial_status,
    expire_trials,
    get_users_with_expiring_trials
)
from cognito_utils import add_user_to_group, remove_user_from_group

logger = logging.getLogger(__name__)

def initialize_user(user_email, user_id, user_tier='Free'):
    """Initialize a new user in the database"""
    try:
        success = create_or_update_user(user_id, user_email, user_tier)
        if success:
            logger.info(f"User {user_email} initialized successfully")
            return True
        else:
            logger.error(f"Failed to initialize user {user_email}")
            return False
    except Exception as e:
        logger.error(f"Error initializing user {user_email}: {e}")
        return False

def get_user_info(user_email):
    """Get comprehensive user information including trial status"""
    try:
        user = get_user_by_email(user_email)
        if not user:
            return None
        
        # Get trial status
        trial_status = check_trial_status(user['user_id'])
        
        # Combine user info with trial status
        user_info = {
            'user_id': user['user_id'],
            'email': user['email'],
            'user_tier': user['user_tier'],
            'created_at': user['created_at'],
            'updated_at': user['updated_at'],
            'trial_status': trial_status
        }
        
        return user_info
        
    except Exception as e:
        logger.error(f"Error getting user info for {user_email}: {e}")
        return None

def start_user_trial(user_email, user_id):
    """Start a Premium trial for a user and update Cognito groups"""
    try:
        # Check if user exists, create if not
        user = get_user_by_email(user_email)
        if not user:
            initialize_user(user_email, user_id, 'Free')
        
        # Start the trial in database
        trial_started = start_premium_trial(user_id)
        if not trial_started:
            return {
                'success': False,
                'error': 'Unable to start trial. Trial may already be used or user not found.'
            }
        
        # Update Cognito groups
        # Remove from free-tier if present
        remove_user_from_group(user_email, 'free-tier')
        
        # Add to premium-trial group
        group_success = add_user_to_group(user_email, 'premium-trial')
        if not group_success:
            logger.warning(f"Failed to add user {user_email} to premium-trial group")
        
        # Get updated trial status
        trial_status = check_trial_status(user_id)
        
        return {
            'success': True,
            'trial_status': trial_status,
            'message': '30-day Premium trial started successfully!'
        }
        
    except Exception as e:
        logger.error(f"Error starting trial for user {user_email}: {e}")
        return {
            'success': False,
            'error': f'Failed to start trial: {str(e)}'
        }

def get_user_trial_status(user_email, user_id):
    """Get detailed trial status for a user"""
    try:
        # Ensure user exists in database
        user = get_user_by_email(user_email)
        if not user:
            initialize_user(user_email, user_id, 'Free')
            user = get_user_by_email(user_email)
        
        # Get trial status
        trial_status = check_trial_status(user_id)
        
        # Enhance with user tier information
        enhanced_status = {
            'user_tier': user['user_tier'],
            'trial_status': trial_status['status'],
            'can_start_trial': trial_status.get('can_start_trial', False),
            'days_remaining': trial_status.get('days_remaining', 0),
            'trial_expires_at': trial_status.get('trial_expires_at'),
            'trial_started_at': trial_status.get('trial_started_at')
        }
        
        return enhanced_status
        
    except Exception as e:
        logger.error(f"Error getting trial status for user {user_email}: {e}")
        return {
            'user_tier': 'Free',
            'trial_status': 'error',
            'can_start_trial': False,
            'days_remaining': 0,
            'error': str(e)
        }

def process_expired_trials():
    """Process all expired trials - downgrade users and update Cognito groups"""
    try:
        # Get users whose trials are expiring today
        expiring_users = get_users_with_expiring_trials(days_ahead=0)
        
        for user in expiring_users:
            logger.info(f"Processing expired trial for user {user['email']}")
            
            # Remove from premium-trial group and add to free-tier
            remove_user_from_group(user['email'], 'premium-trial')
            add_user_to_group(user['email'], 'free-tier')
        
        # Update database to mark trials as expired
        expired_count = expire_trials()
        
        logger.info(f"Processed {expired_count} expired trials")
        return {
            'success': True,
            'expired_count': expired_count,
            'processed_users': len(expiring_users)
        }
        
    except Exception as e:
        logger.error(f"Error processing expired trials: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_trial_reminder_users(days_ahead=3):
    """Get users who should receive trial expiration reminders"""
    try:
        users = get_users_with_expiring_trials(days_ahead)
        reminder_users = []
        
        for user in users:
            reminder_users.append({
                'email': user['email'],
                'user_id': user['user_id'],
                'days_remaining': user['days_remaining'],
                'trial_expires_at': user['trial_expires_at']
            })
        
        return reminder_users
        
    except Exception as e:
        logger.error(f"Error getting trial reminder users: {e}")
        return []

def validate_trial_eligibility(user_email, user_id):
    """Check if a user is eligible to start a Premium trial"""
    try:
        # Get or create user
        user = get_user_by_email(user_email)
        if not user:
            initialize_user(user_email, user_id, 'Free')
            return {'eligible': True, 'reason': 'New user'}
        
        # Check trial status
        trial_status = check_trial_status(user_id)
        
        if trial_status['status'] == 'no_trial' and trial_status.get('can_start_trial', False):
            return {'eligible': True, 'reason': 'No previous trial'}
        elif trial_status['status'] == 'active':
            return {'eligible': False, 'reason': 'Trial already active'}
        elif trial_status['status'] == 'expired' or not trial_status.get('can_start_trial', False):
            return {'eligible': False, 'reason': 'Trial already used'}
        else:
            return {'eligible': False, 'reason': 'Unknown status'}
            
    except Exception as e:
        logger.error(f"Error validating trial eligibility for {user_email}: {e}")
        return {'eligible': False, 'reason': f'Error: {str(e)}'}
