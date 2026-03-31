#!/usr/bin/env python3
"""
Direct login test to see the exact error
"""

import requests
import json

def test_login():
    print("=== DIRECT LOGIN TEST ===")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        print(f"   Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   Health failed: {e}")
        return
    
    # Test 2: Login with detailed error capture
    print("2. Testing login endpoint...")
    try:
        response = requests.post(
            'http://localhost:5000/api/login',
            json={'email': 'test@example.com', 'password': 'test'},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 500:
            data = response.json()
            print(f"   Error details: {data}")
            
            # Test 3: Try creating user first
            print("3. Creating test user...")
            try:
                # This won't work via API since we need auth, but let's try
                register_response = requests.post(
                    'http://localhost:5000/api/register',
                    json={
                        'name': 'Test User',
                        'email': 'test@example.com', 
                        'password': 'test',
                        'role': 'Team'
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                print(f"   Register: {register_response.status_code} - {register_response.text}")
                
                # Try login again
                login_response = requests.post(
                    'http://localhost:5000/api/login',
                    json={'email': 'test@example.com', 'password': 'test'},
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                print(f"   Login after register: {login_response.status_code} - {login_response.text}")
                
            except Exception as e:
                print(f"   Register failed: {e}")
        
        elif response.status_code == 200:
            print("   ✅ Login successful!")
            print(f"   User data: {response.json()}")
        else:
            print(f"   Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   Login test failed: {e}")

if __name__ == '__main__':
    test_login()
