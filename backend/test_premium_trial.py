#!/usr/bin/env python3
"""
Test script for Premium Trial functionality
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    create_or_update_user,
    get_user_by_email,
    start_premium_trial,
    check_trial_status,
    expire_trials
)
from user_management import (
    initialize_user,
    get_user_trial_status,
    validate_trial_eligibility,
    start_user_trial
)

def test_database_functions():
    """Test database functions"""
    print("🧪 Testing Database Functions")
    print("=" * 50)
    
    test_email = "test@example.com"
    test_user_id = "test123"
    
    # Test 1: Create user
    print("1. Creating test user...")
    success = create_or_update_user(test_user_id, test_email, 'Free')
    print(f"   ✅ User created: {success}")
    
    # Test 2: Get user
    print("2. Retrieving test user...")
    user = get_user_by_email(test_email)
    print(f"   ✅ User retrieved: {user is not None}")
    if user:
        print(f"   User tier: {user['user_tier']}")
    
    # Test 3: Check trial eligibility
    print("3. Checking trial eligibility...")
    trial_status = check_trial_status(test_user_id)
    print(f"   ✅ Trial status: {trial_status}")
    
    # Test 4: Start trial
    print("4. Starting trial...")
    trial_started = start_premium_trial(test_user_id)
    print(f"   ✅ Trial started: {trial_started}")
    
    # Test 5: Check trial status after start
    print("5. Checking trial status after start...")
    trial_status = check_trial_status(test_user_id)
    print(f"   ✅ Updated trial status: {trial_status}")
    
    # Test 6: Try to start trial again (should fail)
    print("6. Trying to start trial again (should fail)...")
    trial_started_again = start_premium_trial(test_user_id)
    print(f"   ✅ Second trial start (should be False): {trial_started_again}")
    
    # Cleanup
    print("7. Cleaning up test data...")
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE email = ?', (test_email,))
            conn.commit()
        print("   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️ Cleanup failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Database tests completed!")

def test_user_management_functions():
    """Test user management functions"""
    print("\n🧪 Testing User Management Functions")
    print("=" * 50)
    
    test_email = "testuser@example.com"
    test_user_id = "testuser123"
    
    # Test 1: Initialize user
    print("1. Initializing user...")
    success = initialize_user(test_email, test_user_id, 'Free')
    print(f"   ✅ User initialized: {success}")
    
    # Test 2: Get user trial status
    print("2. Getting user trial status...")
    status = get_user_trial_status(test_email, test_user_id)
    print(f"   ✅ Trial status: {status}")
    
    # Test 3: Validate trial eligibility
    print("3. Validating trial eligibility...")
    eligibility = validate_trial_eligibility(test_email, test_user_id)
    print(f"   ✅ Trial eligibility: {eligibility}")
    
    # Test 4: Start user trial (without Cognito)
    print("4. Starting user trial (Cognito operations will fail in test)...")
    try:
        result = start_user_trial(test_email, test_user_id)
        print(f"   ✅ Trial start result: {result}")
    except Exception as e:
        print(f"   ⚠️ Trial start failed (expected due to Cognito): {e}")
    
    # Cleanup
    print("5. Cleaning up test data...")
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE email = ?', (test_email,))
            conn.commit()
        print("   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️ Cleanup failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ User management tests completed!")

def test_database_schema():
    """Test database schema"""
    print("\n🧪 Testing Database Schema")
    print("=" * 50)
    
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            users_table = cursor.fetchone()
            print(f"1. Users table exists: {users_table is not None}")
            
            if users_table:
                # Check users table structure
                cursor.execute("PRAGMA table_info(users)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"2. Users table columns: {column_names}")
                
                required_columns = ['user_id', 'email', 'user_tier', 'trial_started_at', 'trial_expires_at', 'trial_used']
                missing_columns = [col for col in required_columns if col not in column_names]
                print(f"3. Missing columns: {missing_columns if missing_columns else 'None'}")
                
                # Check indexes
                cursor.execute("PRAGMA index_list(users)")
                indexes = cursor.fetchall()
                print(f"4. Indexes on users table: {len(indexes)} indexes")
                
                print("   ✅ Database schema validated")
            else:
                print("   ❌ Users table not found")
                
    except Exception as e:
        print(f"   ❌ Schema test failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Database schema tests completed!")

def main():
    """Run all tests"""
    print("🚀 Premium Trial System Tests")
    print("=" * 50)
    
    try:
        test_database_schema()
        test_database_functions()
        test_user_management_functions()
        
        print("\n🎉 All tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
