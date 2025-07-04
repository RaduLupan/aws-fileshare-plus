# auto_confirm_user.py

import json

def handler(event, context):
    """
    This function is triggered by Cognito's Pre-Sign-Up hook.
    In dev environment, it automatically confirms users and verifies their email
    to enable password reset functionality.
    """
    
    print(f"Pre-sign-up trigger called for user: {event.get('userName', 'unknown')}")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Auto-confirm the user and auto-verify email for dev environment
    # This enables immediate login and password reset functionality
    event['response']['autoConfirmUser'] = True
    event['response']['autoVerifyEmail'] = True
    
    print("Auto-confirming user and verifying email for dev environment")
    
    return event
