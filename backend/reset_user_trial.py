#!/usr/bin/env python3
"""
Utility script to reset a user's trial status
"""

import sqlite3
import sys
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'url_shortener.db')

def reset_user_trial(email):
    """Reset a user's trial status to allow them to start a trial again"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT user_id, email, trial_used FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if not user:
                print(f"User {email} not found in database")
                return False
            
            user_id, user_email, trial_used = user
            print(f"Found user: {user_id}, email: {user_email}, trial_used: {trial_used}")
            
            # Reset trial status
            cursor.execute('''
                UPDATE users 
                SET trial_used = FALSE,
                    trial_started_at = NULL,
                    trial_expires_at = NULL,
                    user_tier = 'Free',
                    updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            ''', (email,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"Successfully reset trial status for {email}")
                
                # Verify the reset
                cursor.execute('SELECT user_tier, trial_used, trial_started_at, trial_expires_at FROM users WHERE email = ?', (email,))
                updated_user = cursor.fetchone()
                print(f"Updated user status: tier={updated_user[0]}, trial_used={updated_user[1]}, trial_started={updated_user[2]}, trial_expires={updated_user[3]}")
                
                return True
            else:
                print(f"No rows updated for {email}")
                return False
                
    except Exception as e:
        print(f"Error resetting trial for {email}: {e}")
        return False

def list_all_users():
    """List all users in the database"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, email, user_tier, trial_used, trial_started_at, trial_expires_at FROM users')
            users = cursor.fetchall()
            
            print("All users in database:")
            print("-" * 80)
            for user in users:
                user_id, email, tier, trial_used, trial_started, trial_expires = user
                print(f"ID: {user_id}")
                print(f"Email: {email}")
                print(f"Tier: {tier}")
                print(f"Trial Used: {trial_used}")
                print(f"Trial Started: {trial_started}")
                print(f"Trial Expires: {trial_expires}")
                print("-" * 40)
                
    except Exception as e:
        print(f"Error listing users: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 reset_user_trial.py list                   # List all users")
        print("  python3 reset_user_trial.py reset <email>         # Reset trial for specific user")
        print("  python3 reset_user_trial.py reset radu@lupan.ca   # Example")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_all_users()
    elif command == "reset" and len(sys.argv) == 3:
        email = sys.argv[2]
        success = reset_user_trial(email)
        if success:
            print(f"\n✅ Trial status reset successfully for {email}")
            print("The user should now be able to start a trial.")
        else:
            print(f"\n❌ Failed to reset trial status for {email}")
    else:
        print("Invalid command. Use 'list' or 'reset <email>'")
        sys.exit(1)