# Simple trial functions to get the trial system working
from datetime import datetime, timedelta
import sqlite3
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'url_shortener.db')

def simple_create_or_update_user(user_id, email, user_tier='Free'):
    """Simple user creation/update function"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, email, user_tier, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, email, user_tier))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error creating/updating user: {e}")
        return False

def simple_get_user_by_email(email):
    """Simple user lookup by email"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            if row:
                # Get column names
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

def simple_start_trial(user_id, user_email):
    """Simple trial start function"""
    try:
        # Ensure trial columns exist
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check if trial columns exist, add if missing
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'trial_started_at' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP NULL')
            if 'trial_expires_at' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP NULL')
            if 'trial_used' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT FALSE')
            
            # Start trial
            expires_at = datetime.now() + timedelta(days=30)
            cursor.execute('''
                UPDATE users 
                SET user_tier = 'premium-trial',
                    trial_started_at = CURRENT_TIMESTAMP,
                    trial_expires_at = ?,
                    trial_used = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? OR email = ?
            ''', (expires_at.isoformat(), user_id, user_email))
            
            if cursor.rowcount == 0:
                # User doesn't exist, create them
                cursor.execute('''
                    INSERT INTO users (user_id, email, user_tier, trial_started_at, trial_expires_at, trial_used)
                    VALUES (?, ?, 'premium-trial', CURRENT_TIMESTAMP, ?, TRUE)
                ''', (user_id, user_email, expires_at.isoformat()))
            
            conn.commit()
            return {
                'success': True,
                'trial_expires_at': expires_at.isoformat(),
                'days_remaining': 30
            }
            
    except Exception as e:
        print(f"Error starting trial: {e}")
        return {'success': False, 'error': str(e)}

def simple_add_user_to_group(user_email, group_name):
    """Simple Cognito group addition (placeholder)"""
    try:
        import boto3
        cognito = boto3.client('cognito-idp')
        
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        if not user_pool_id:
            print("Warning: No COGNITO_USER_POOL_ID found")
            return False
            
        cognito.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=user_email,
            GroupName=group_name
        )
        return True
    except Exception as e:
        print(f"Error adding user to group {group_name}: {e}")
        return False

def simple_remove_user_from_group(user_email, group_name):
    """Simple Cognito group removal (placeholder)"""
    try:
        import boto3
        cognito = boto3.client('cognito-idp')
        
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        if not user_pool_id:
            print("Warning: No COGNITO_USER_POOL_ID found")
            return False
            
        cognito.admin_remove_user_from_group(
            UserPoolId=user_pool_id,
            Username=user_email,
            GroupName=group_name
        )
        return True
    except Exception as e:
        print(f"Error removing user from group {group_name}: {e}")
        return False
