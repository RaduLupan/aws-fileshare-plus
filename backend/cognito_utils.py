"""
AWS Cognito utilities for user group management
"""
import boto3
import os
import logging

logger = logging.getLogger(__name__)

# Cognito configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')

def get_cognito_client():
    """Get Cognito IDP client"""
    return boto3.client('cognito-idp', region_name=AWS_REGION)

def add_user_to_group(user_email, group_name):
    """Add a user to a Cognito group"""
    try:
        cognito_client = get_cognito_client()
        
        cognito_client.admin_add_user_to_group(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=user_email,
            GroupName=group_name
        )
        
        logger.info(f"Added user '{user_email}' to '{group_name}' group")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add user '{user_email}' to '{group_name}' group: {e}")
        return False

def remove_user_from_group(user_email, group_name):
    """Remove a user from a Cognito group"""
    try:
        cognito_client = get_cognito_client()
        
        cognito_client.admin_remove_user_from_group(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=user_email,
            GroupName=group_name
        )
        
        logger.info(f"Removed user '{user_email}' from '{group_name}' group")
        return True
        
    except cognito_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'UserNotInGroupException':
            logger.info(f"User '{user_email}' was not in '{group_name}' group")
            return True  # Consider this a success since the end state is correct
        else:
            logger.error(f"Failed to remove user '{user_email}' from '{group_name}' group: {e}")
            return False
    except Exception as e:
        logger.error(f"Failed to remove user '{user_email}' from '{group_name}' group: {e}")
        return False

def get_user_groups(user_email):
    """Get all groups for a user"""
    try:
        cognito_client = get_cognito_client()
        
        response = cognito_client.admin_list_groups_for_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=user_email
        )
        
        groups = [group['GroupName'] for group in response.get('Groups', [])]
        logger.info(f"User '{user_email}' is in groups: {groups}")
        return groups
        
    except Exception as e:
        logger.error(f"Failed to get groups for user '{user_email}': {e}")
        return []

def move_user_to_trial_group(user_email):
    """Move user from free-tier to premium-trial group"""
    try:
        # Remove from free-tier group (if present)
        remove_user_from_group(user_email, 'free-tier')
        
        # Add to premium-trial group
        success = add_user_to_group(user_email, 'premium-trial')
        
        if success:
            logger.info(f"Successfully moved user '{user_email}' to premium-trial group")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to move user '{user_email}' to trial group: {e}")
        return False

def move_user_to_free_group(user_email):
    """Move user from premium-trial back to free-tier group"""
    try:
        # Remove from premium-trial group
        remove_user_from_group(user_email, 'premium-trial')
        
        # Add to free-tier group
        success = add_user_to_group(user_email, 'free-tier')
        
        if success:
            logger.info(f"Successfully moved user '{user_email}' to free-tier group")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to move user '{user_email}' to free group: {e}")
        return False

def move_user_to_premium_group(user_email):
    """Move user to premium-tier group (for paid upgrades)"""
    try:
        # Remove from any trial or free groups
        remove_user_from_group(user_email, 'free-tier')
        remove_user_from_group(user_email, 'premium-trial')
        
        # Add to premium-tier group
        success = add_user_to_group(user_email, 'premium-tier')
        
        if success:
            logger.info(f"Successfully moved user '{user_email}' to premium-tier group")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to move user '{user_email}' to premium group: {e}")
        return False

def ensure_trial_group_exists():
    """Ensure the premium-trial group exists in Cognito"""
    try:
        cognito_client = get_cognito_client()
        
        # Try to describe the group
        try:
            cognito_client.describe_group(
                GroupName='premium-trial',
                UserPoolId=COGNITO_USER_POOL_ID
            )
            logger.info("premium-trial group already exists")
            return True
            
        except cognito_client.exceptions.ResourceNotFoundException:
            # Group doesn't exist, create it
            cognito_client.create_group(
                GroupName='premium-trial',
                UserPoolId=COGNITO_USER_POOL_ID,
                Description='Users on 30-day Premium trial',
                Precedence=50  # Between free-tier (100) and premium-tier (10)
            )
            logger.info("Created premium-trial group")
            return True
            
    except Exception as e:
        logger.error(f"Failed to ensure premium-trial group exists: {e}")
        return False

def validate_cognito_setup():
    """Validate that all required Cognito groups exist"""
    try:
        cognito_client = get_cognito_client()
        
        required_groups = ['free-tier', 'premium-trial', 'premium-tier']
        existing_groups = []
        
        # List all groups
        response = cognito_client.list_groups(UserPoolId=COGNITO_USER_POOL_ID)
        group_names = [group['GroupName'] for group in response.get('Groups', [])]
        
        for group in required_groups:
            if group in group_names:
                existing_groups.append(group)
            else:
                logger.warning(f"Required group '{group}' does not exist")
        
        logger.info(f"Existing groups: {existing_groups}")
        return {
            'valid': len(existing_groups) == len(required_groups),
            'existing_groups': existing_groups,
            'missing_groups': [g for g in required_groups if g not in existing_groups]
        }
        
    except Exception as e:
        logger.error(f"Failed to validate Cognito setup: {e}")
        return {
            'valid': False,
            'error': str(e)
        }
