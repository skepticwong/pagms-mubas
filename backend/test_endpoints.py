#!/usr/bin/env python3
"""
Quick test for dashboard endpoints
"""

import requests
import json

def test_dashboard_endpoints():
    """Test dashboard endpoints with simplified data"""
    print("🧪 Testing Dashboard Endpoints")
    print("=" * 50)
    
    endpoints = [
        ("/api/dashboard/test", "Test Endpoint"),
        ("/api/dashboard/milestone/27/impact", "Milestone 27 Impact"),
        ("/api/dashboard/milestone/27/operational", "Milestone 27 Operational"),
        ("/api/dashboard/milestone/28/impact", "Milestone 28 Impact"),
        ("/api/dashboard/milestone/28/operational", "Milestone 28 Operational")
    ]
    
    for endpoint, description in endpoints:
        print(f"\n📍 Testing: {description}")
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            print(f"✅ Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Data received: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error - Backend not running")
        except requests.exceptions.Timeout:
            print("❌ Timeout Error")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete!")

if __name__ == "__main__":
    test_dashboard_endpoints()
