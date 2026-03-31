
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_grants_api():
    # 1. Login to get session
    session = requests.Session()
    print("Attempting login...")
    login_data = {"email": "pi@mubas.ac.mw", "password": "mubas123"}
    resp = session.post(f"{BASE_URL}/login", json=login_data)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return

    print("Login successful.")
    
    # 2. Call /grants
    print("Calling /api/grants...")
    resp = session.get(f"{BASE_URL}/grants")
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"Grants count: {len(data.get('grants', []))}")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {resp.text}")

if __name__ == "__main__":
    test_grants_api()
