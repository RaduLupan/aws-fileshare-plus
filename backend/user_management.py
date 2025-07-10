"""
User management functions for Premium Trial system
"""
import sqlite3
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'url_shortener.db')

def get_user_trial_status(user_email, user_id):
    """Get comprehensive trial status for a user"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # First, ensure the user exists in the database
            cursor.execute('SELECT * FROM users WHERE email = ? OR user_id = ?', (user_email, user_id))
            user = cursor.fetchone()
            
            if not user:
                # User doesn't exist, create them as a new free tier user
                cursor.execute('''
                    INSERT INTO users (user_id, email, user_tier, trial_used, created_at, updated_at)
                    VALUES (?, ?, 'Free', FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, user_email))
                conn.commit()
                
                return {
                    'user_tier': 'Free',
                    'trial_status': 'not_started',
                    'can_start_trial': True,
                    'days_remaining': 0,
                    'trial_started_at': None,
                    'trial_expires_at': None
                }
            
            user_dict = dict(user)
            
            # Check if trial was never started
            if not user_dict.get('trial_started_at'):
                return {
                    'user_tier': user_dict.get('user_tier', 'Free'),
                    'trial_status': 'not_started',
                    'can_start_trial': not user_dict.get('trial_used', False),
                    'days_remaining': 0,
                    'trial_started_at': None,
                    'trial_expires_at': None
                }
            
            # Check if trial has expired
            trial_expires_at = user_dict.get('trial_expires_at')
            if trial_expires_at:
                try:
                    # Parse the trial expiration date
                    if isinstance(trial_expires_at, str):
                        expires_dt = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
                    else:
                        expires_dt = trial_expires_at
                    
                    now = datetime.now()
                    if expires_dt.tzinfo:
                        # Make now timezone-aware if expires_dt is timezone-aware
                        from datetime import timezone
                        now = now.replace(tzinfo=timezone.utc)
                    
                    if now > expires_dt:
                        # Trial has expired
                        return {
                            'user_tier': user_dict.get('user_tier', 'Free'),
                            'trial_status': 'expired',
                            'can_start_trial': False,
                            'days_remaining': 0,
                            'trial_started_at': user_dict.get('trial_started_at'),
                            'trial_expires_at': user_dict.get('trial_expires_at')
                        }
                    else:
                        # Trial is still active
                        days_remaining = (expires_dt - now).days
                        return {
                            'user_tier': user_dict.get('user_tier', 'Free'),
                            'trial_status': 'active',
                            'can_start_trial': False,
                            'days_remaining': max(0, days_remaining),
                            'trial_started_at': user_dict.get('trial_started_at'),
                            'trial_expires_at': user_dict.get('trial_expires_at')
                        }
                except Exception as date_error:
                    logger.error(f"Error parsing trial dates for user {user_email}: {date_error}")
            
            # Fallback - trial status unclear
            return {
                'user_tier': user_dict.get('user_tier', 'Free'),
                'trial_status': 'not_started',
                'can_start_trial': not user_dict.get('trial_used', False),
                'days_remaining': 0,
                'trial_started_at': user_dict.get('trial_started_at'),
                'trial_expires_at': user_dict.get('trial_expires_at')
            }
            
    except Exception as e:
        logger.error(f"Error getting trial status for user {user_email}: {e}")
        # Return safe default for new users
        return {
            'user_tier': 'Free',
            'trial_status': 'not_started',
            'can_start_trial': True,
            'days_remaining': 0,
            'trial_started_at': None,
            'trial_expires_at': None
        }

def validate_trial_eligibility(user_email, user_id):
    """Check if user is eligible to start a Premium trial"""
    try:
        trial_status = get_user_trial_status(user_email, user_id)
        
        if trial_status['can_start_trial']:
            return {
                'eligible': True,
                'reason': 'User has not used trial yet'
            }
        else:
            return {
                'eligible': False,
                'reason': 'Trial already used or currently active'
            }
            
    except Exception as e:
        logger.error(f"Error validating trial eligibility for {user_email}: {e}")
        return {
            'eligible': False,
            'reason': f'Error checking eligibility: {str(e)}'
        }

def start_user_trial(user_email, user_id):
    """Start a 30-day Premium trial for a user"""
    try:
        # Check eligibility first
        eligibility = validate_trial_eligibility(user_email, user_id)
        if not eligibility['eligible']:
            return {
                'success': False,
                'error': eligibility['reason']
            }
        
        # Use the simple trial functions
        from simple_trial_functions import simple_start_trial, simple_add_user_to_group, simple_remove_user_from_group
        
        # Start the trial in database
        result = simple_start_trial(user_id, user_email)
        
        if result['success']:
            # Try to update Cognito groups
            try:
                simple_remove_user_from_group(user_email, 'free-tier')
                simple_add_user_to_group(user_email, 'premium-trial')
                logger.info(f"Cognito groups updated for {user_email}")
            except Exception as cognito_err:
                logger.warning(f"Cognito group update failed: {cognito_err}")
                
            return {
                'success': True,
                'message': 'Trial started successfully',
                'trial_status': {
                    'trial_expires_at': result['trial_expires_at'],
                    'days_remaining': result['days_remaining']
                }
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"Error starting trial for user {user_email}: {e}")
        return {
            'success': False,
            'error': f'Failed to start trial: {str(e)}'
        }

def process_expired_trials():
    """Process and clean up expired trials"""
    try:
        from database import expire_trials
        expired_count = expire_trials()
        
        return {
            'success': True,
            'expired_count': expired_count,
            'message': f'Processed {expired_count} expired trials'
        }
        
    except Exception as e:
        logger.error(f"Error processing expired trials: {e}")
        return {
            'success': False,
            'error': f'Failed to process expired trials: {str(e)}'
        }