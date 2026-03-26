import requests
import json

def test_backend():
    base_url = "http://localhost:5000"
    
    print("Testing PAGMS Backend API...")
    print(f"Base URL: {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"Health check: {response.status_code}")
    except Exception as e:
        print(f"Health check failed: {e}")
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
        print(f"Login test failed: {e}")
        return False

if __name__ == "__main__":
    test_backend()
