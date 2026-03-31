#!/usr/bin/env python3
"""
Simple backend server test
"""

import requests
import time

def test_backend():
    """Test if backend is responding"""
    print("🧪 Testing Backend Server Response")
    print("=" * 50)
    
    try:
        # Test with very short timeout
        print("📍 Testing basic connectivity...")
        response = requests.get('http://localhost:5000/api/dashboard/test', timeout=3)
        print(f"⏱️ Response time: {response.elapsed.total_seconds()}")
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - backend might be hanging")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Backend Test Complete!")

if __name__ == "__main__":
    test_backend()
