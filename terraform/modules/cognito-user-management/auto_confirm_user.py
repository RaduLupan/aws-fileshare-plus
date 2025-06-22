# auto_confirm_user.py

import json

def handler(event, context):
    """
    This function is triggered by Cognito's Pre-Sign-Up hook.
    In dev environment, it automatically confirms users without email verification.
    """
    
    print(f"Pre-sign-up trigger called for user: {event.get('userName', 'unknown')}")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Auto-confirm the user but don't auto-verify email since we're using email as alias
    # This bypasses the need for email confirmation
    event['response']['autoConfirmUser'] = True
    # Don't set autoVerifyEmail when using email as alias attribute
    # event['response']['autoVerifyEmail'] = True
    
    print("Auto-confirming user")
    
    return event
