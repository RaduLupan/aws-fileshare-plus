# add_to_group.py

import boto3
import os

def handler(event, context):
    """
    This function is triggered by Cognito's Post-Confirmation hook.
    It automatically adds the newly confirmed user to the 'free-tier' group.
    """
    
    # Get the user pool ID and username from the Cognito event
    user_pool_id = event['userPoolId']
    user_name = event['userName']
    
    # Get the name of the group from an environment variable
    free_tier_group_name = os.environ['FREE_TIER_GROUP_NAME']
    
    print(f"Attempting to add user '{user_name}' to group '{free_tier_group_name}' in user pool '{user_pool_id}'")
    
    cognito_client = boto3.client('cognito-idp')
    
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=user_name,
            GroupName=free_tier_group_name
        )
        print("Successfully added user to group.")
    except Exception as e:
        print(f"Error adding user to group: {e}")
        # Raising the exception will cause Cognito to see the trigger as failed.
        raise e
        
    # Return the event object back to Cognito
    return event
