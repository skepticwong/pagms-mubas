#!/usr/bin/env python3
"""
Simple API test to debug the 500 errors
"""

import requests
import json

def test_api_endpoints():
    """Test API endpoints and capture detailed error information"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 API Endpoint Debug Test")
    print("=" * 40)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text[:100]}")
        else:
            print(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: Login
    print("\n🔐 Testing login...")
    try:
        login_response = requests.post(f"{base_url}/api/login",
                                      json={"email": "admin@pagms.com", "password": "password123"},
                                      timeout=5)
        print(f"Login: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text[:300]}")
            return False
        
        print("✅ Login successful")
        
        # Get session cookies
        session = requests.Session()
        session.post(f"{base_url}/api/login",
                    json={"email": "admin@pagms.com", "password": "password123"})
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test 3: Test each endpoint with detailed error capture
    endpoints = [
        ("/api/me", "User info"),
        ("/api/grants", "Grants"),
        ("/api/deliverables?status=pending", "Deliverables"),
        ("/api/expenses", "Expenses"),
        ("/api/tasks", "Tasks"),
        ("/api/pi-dashboard/action-items", "Action items")
    ]
    
    print("\n📡 Testing API endpoints:")
    
    for endpoint, name in endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}", timeout=10)
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"{status_icon} {name}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'grants' in data:
                        print(f"    📊 Grants: {len(data['grants'])}")
                    elif 'submissions' in data:
                        print(f"    📋 Submissions: {len(data['submissions'])}")
                    elif 'expenses' in data:
                        print(f"    💰 Expenses: {len(data['expenses'])}")
                    elif 'tasks' in data:
                        print(f"    📝 Tasks: {len(data['tasks'])}")
                    elif 'id' in data:
                        print(f"    👤 User ID: {data['id']}")
                    else:
                        print(f"    🔑 Data keys: {list(data.keys())}")
                except json.JSONDecodeError:
                    print(f"    ⚠️  Invalid JSON response")
            else:
                print(f"    🚨 Error: {response.text[:400]}")
                
        except requests.exceptions.Timeout:
            print(f"❌ {name}: Timeout")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Connection error")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    return True

if __name__ == "__main__":
    test_api_endpoints()
