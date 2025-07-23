#!/usr/bin/env python3
"""
DynamoDB Migration Script for AWS FileShare Plus
Creates the necessary DynamoDB tables for user management and trial system
"""

import boto3
import os
import sys
from botocore.exceptions import ClientError

def create_users_table(dynamodb, table_name):
    """Create the users table for storing user information and trial status"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Created table: {table_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"ℹ️  Table {table_name} already exists")
            return True
        else:
            print(f"❌ Error creating table {table_name}: {e}")
            return False

def create_short_urls_table(dynamodb, table_name):
    """Create the short_urls table for URL shortening functionality"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'short_code',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'short_code',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user-urls-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Created table: {table_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"ℹ️  Table {table_name} already exists")
            return True
        else:
            print(f"❌ Error creating table {table_name}: {e}")
            return False

def main():
    """Main migration function"""
    print("🚀 Starting DynamoDB Migration for AWS FileShare Plus")
    print("=" * 60)
    
    # Get AWS region from environment or use default
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    print(f"📍 Using AWS Region: {aws_region}")
    
    # Initialize DynamoDB client
    try:
        dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        print("✅ DynamoDB client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize DynamoDB client: {e}")
        sys.exit(1)
    
    # Define table names
    project_name = os.getenv('PROJECT_NAME', 'aws-fileshare-plus')
    environment = os.getenv('ENVIRONMENT', 'prod')
    
    users_table_name = f"{project_name}-{environment}-users"
    short_urls_table_name = f"{project_name}-{environment}-short-urls"
    
    print(f"📋 Table names:")
    print(f"   - Users: {users_table_name}")
    print(f"   - Short URLs: {short_urls_table_name}")
    print()
    
    # Create tables
    success_count = 0
    
    print("🔨 Creating DynamoDB tables...")
    print("-" * 40)
    
    if create_users_table(dynamodb, users_table_name):
        success_count += 1
    
    if create_short_urls_table(dynamodb, short_urls_table_name):
        success_count += 1
    
    print("-" * 40)
    
    if success_count == 2:
        print("🎉 Migration completed successfully!")
        print()
        print("📝 Next steps:")
        print("1. Update your ECS task definition to include:")
        print("   - USE_DYNAMODB=true")
        print("   - DYNAMODB_USERS_TABLE=" + users_table_name)
        print("   - DYNAMODB_SHORT_URLS_TABLE=" + short_urls_table_name)
        print("2. Redeploy your ECS service")
        print("3. Test the trial functionality")
    else:
        print("❌ Migration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 