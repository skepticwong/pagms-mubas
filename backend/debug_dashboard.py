#!/usr/bin/env python3
"""
Debug script for testing dashboard endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_endpoint(endpoint, description):
    """Test a specific endpoint"""
    print(f"\n🧪 Testing: {description}")
    print(f"📍 URL: {BASE_URL}{endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2)[:300]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Backend server not running")
    except requests.exceptions.Timeout:
        print("❌ Timeout - Server took too long to respond")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🚀 PAGMS Dashboard Debug Tool")
    print("=" * 50)
    
    # Test basic connectivity
    test_endpoint("/grants", "Basic Grants API")
    
    # Test dashboard endpoints
    test_endpoint("/dashboard/test", "Dashboard Test Endpoint")
    test_endpoint("/dashboard/milestone/27/impact", "Milestone 27 Impact Scorecard")
    test_endpoint("/dashboard/milestone/27/operational", "Milestone 27 Operational Metrics")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Complete!")

if __name__ == "__main__":
    main()
