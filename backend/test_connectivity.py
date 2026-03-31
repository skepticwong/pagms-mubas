#!/usr/bin/env python3
"""
Quick network connectivity test
"""

import requests

def test_connectivity():
    """Test different connection methods"""
    print("🌐 Testing Network Connectivity")
    print("=" * 50)
    
    # Test 1: Direct localhost connection
    try:
        response = requests.get('http://localhost:5000/api/dashboard/test', timeout=5)
        print(f"✅ Direct localhost: {response.status_code}")
    except Exception as e:
        print(f"❌ Direct localhost failed: {e}")
    
    # Test 2: Check what IP frontend is using
    try:
        response = requests.get('http://192.168.108.203:34028/api/dashboard/test', timeout=5)
        print(f"✅ External IP: {response.status_code}")
    except Exception as e:
        print(f"❌ External IP failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Connectivity Test Complete!")
    print("\n📋 SOLUTIONS:")
    print("1. Ensure frontend is running on localhost:5173")
    print("2. Clear browser cache and hard refresh")
    print("3. Check if any proxy/VPN is interfering")
    print("4. Restart both frontend and backend servers")

if __name__ == "__main__":
    test_connectivity()
