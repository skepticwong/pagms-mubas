#!/usr/bin/env python3
import requests
import json

def test_backend():
    base_url = "http://localhost:5000"
    
    print("Testing PAGMS Backend CORS...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/me", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"❌ Backend returned: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test login endpoint
    try:
        login_data = {
            "email": "pi@mubas.ac.mw",
            "password": "mubas123"
        }
        response = requests.post(f"{base_url}/api/login", json=login_data, timeout=5)
        print(f"Login attempt: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Login successful: {user_data.get('name')} ({user_data.get('role')})")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

if __name__ == "__main__":
    test_backend()
