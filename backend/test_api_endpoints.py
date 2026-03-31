#!/usr/bin/env python3
"""
Test API endpoints with proper authentication
"""

import requests
import sys

def test_endpoints():
    """Test all API endpoints with authentication"""
    base_url = "http://localhost:5000"
    
    # Create session for authentication
    session = requests.Session()
    
    # First, login
    print("🔐 Logging in...")
    login_response = session.post(f"{base_url}/api/login", 
                                 json={"email": "admin@pagms.com", "password": "admin123"})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    print("✅ Login successful")
    
    # Test endpoints
    endpoints = [
        ("/api/me", "User info"),
        ("/api/grants", "Grants"),
        ("/api/deliverables?status=pending", "Pending deliverables"),
        ("/api/expenses", "Expenses"),
        ("/api/tasks", "Tasks"),
        ("/api/pi-dashboard/action-items", "PI action items")
    ]
    
    print("\n🧪 Testing API endpoints:")
    all_success = True
    
    for endpoint, description in endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {description}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Show data summary
                if 'grants' in data:
                    print(f"    Grants: {len(data['grants'])}")
                elif 'submissions' in data:
                    print(f"    Submissions: {len(data['submissions'])}")
                elif 'expenses' in data:
                    print(f"    Expenses: {len(data['expenses'])}")
                elif 'tasks' in data:
                    print(f"    Tasks: {len(data['tasks'])}")
                elif 'id' in data:
                    print(f"    User ID: {data['id']}")
                else:
                    print(f"    Data keys: {list(data.keys())}")
            else:
                print(f"    Error: {response.text[:300]}")
                all_success = False
                
        except requests.exceptions.Timeout:
            print(f"❌ {description}: Timeout")
            all_success = False
        except Exception as e:
            print(f"❌ {description}: {e}")
            all_success = False
    
    return all_success

if __name__ == "__main__":
    success = test_endpoints()
    if success:
        print("\n🎉 All API endpoints working correctly!")
    else:
        print("\n💥 Some API endpoints failed")
    sys.exit(0 if success else 1)
