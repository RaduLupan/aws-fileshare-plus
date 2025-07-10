#!/usr/bin/env python3
"""
DynamoDB Migration Script - Replace SQLite with DynamoDB for Production
"""

import boto3
import json
from datetime import datetime
import os
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def create_tables():
    """Create DynamoDB tables for users and URL mappings"""
    
    # Users table
    try:
        users_table = dynamodb.create_table(
            TableName='fileshare-users',
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'
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
            BillingMode='PAY_PER_REQUEST',
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
                    }
                }
            ]
        )
        print("✅ Users table created successfully")
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print("ℹ️  Users table already exists")
        else:
            print(f"❌ Error creating users table: {e}")
    
    # URL mappings table
    try:
        urls_table = dynamodb.create_table(
            TableName='fileshare-urls',
            KeySchema=[
                {
                    'AttributeName': 'short_code',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'short_code',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_by_user',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'created_by_user',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ]
        )
        print("✅ URL mappings table created successfully")
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print("ℹ️  URL mappings table already exists")
        else:
            print(f"❌ Error creating URL mappings table: {e}")

def migrate_sqlite_to_dynamodb():
    """Migrate existing SQLite data to DynamoDB"""
    import sqlite3
    
    # Check if SQLite database exists
    sqlite_path = os.path.join(os.path.dirname(__file__), 'url_shortener.db')
    if not os.path.exists(sqlite_path):
        print("ℹ️  No SQLite database found, skipping migration")
        return
    
    print("📦 Migrating data from SQLite to DynamoDB...")
    
    users_table = dynamodb.Table('fileshare-users')
    urls_table = dynamodb.Table('fileshare-urls')
    
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Migrate users
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        
        for user in users:
            user_dict = dict(user)
            # Convert None values and handle datetime
            item = {
                'user_id': user_dict['user_id'],
                'email': user_dict['email'],
                'user_tier': user_dict['user_tier'] or 'Free',
                'trial_used': bool(user_dict['trial_used']),
                'created_at': user_dict['created_at'] or datetime.now().isoformat(),
                'updated_at': user_dict['updated_at'] or datetime.now().isoformat()
            }
            
            # Add trial dates if they exist
            if user_dict['trial_started_at']:
                item['trial_started_at'] = user_dict['trial_started_at']
            if user_dict['trial_expires_at']:
                item['trial_expires_at'] = user_dict['trial_expires_at']
            
            try:
                users_table.put_item(Item=item)
                print(f"✅ Migrated user: {user_dict['email']}")
            except Exception as e:
                print(f"❌ Error migrating user {user_dict['email']}: {e}")
        
        # Migrate URL mappings
        cursor.execute('SELECT * FROM url_mappings')
        urls = cursor.fetchall()
        
        for url in urls:
            url_dict = dict(url)
            item = {
                'short_code': url_dict['short_code'],
                'full_url': url_dict['full_url'],
                'created_at': url_dict['created_at'] or datetime.now().isoformat(),
                'expires_in_days': url_dict['expires_in_days'] or 7,
                'click_count': url_dict['click_count'] or 0
            }
            
            # Add optional fields
            if url_dict['expires_at']:
                item['expires_at'] = url_dict['expires_at']
            if url_dict['created_by_user']:
                item['created_by_user'] = url_dict['created_by_user']
            if url_dict['file_key']:
                item['file_key'] = url_dict['file_key']
            if url_dict['filename']:
                item['filename'] = url_dict['filename']
            
            try:
                urls_table.put_item(Item=item)
                print(f"✅ Migrated URL: {url_dict['short_code']}")
            except Exception as e:
                print(f"❌ Error migrating URL {url_dict['short_code']}: {e}")

if __name__ == "__main__":
    print("🚀 Starting DynamoDB migration...")
    create_tables()
    
    # Wait for tables to be created
    print("⏳ Waiting for tables to be active...")
    users_table = dynamodb.Table('fileshare-users')
    urls_table = dynamodb.Table('fileshare-urls')
    
    users_table.wait_until_exists()
    urls_table.wait_until_exists()
    
    print("✅ Tables are ready!")
    
    # Migrate existing data
    migrate_sqlite_to_dynamodb()
    
    print("🎉 Migration completed!")
    print("\n📋 Next steps:")
    print("1. Update your backend code to use DynamoDB")
    print("2. Set AWS_REGION environment variable")
    print("3. Deploy with updated code")
    print("4. Test the trial button functionality")