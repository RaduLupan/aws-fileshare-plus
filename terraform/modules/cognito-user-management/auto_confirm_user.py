# auto_confirm_user.py

import json

def handler(event, context):
    """
    This function is triggered by Cognito's Pre-Sign-Up hook.
    In dev environment, it automatically confirms users without email verification.
    """
    
    print(f"Pre-sign-up trigger called for user: {event.get('userName', 'unknown')}")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Auto-confirm the user and mark email as verified
    # This bypasses the need for email confirmation
    event['response']['autoConfirmUser'] = True
    event['response']['autoVerifyEmail'] = True
    
    print("Auto-confirming user and marking email as verified")
    
    return event
