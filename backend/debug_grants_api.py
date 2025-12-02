
import requests
import json

# 1. Login as PI
print("Logging in as PI...")
session = requests.Session()
try:
    login_res = session.post('http://127.0.0.1:5000/api/login', json={'email': 'pi@mubas.ac.mw', 'password': 'mubas123'}, timeout=5)
    if login_res.status_code != 200:
        print(f"Login Failed: {login_res.status_code} {login_res.text}")
        exit(1)
    print("Login successful.")
except Exception as e:
    print(f"Login Exception: {e}")
    exit(1)

endpoints = [
    'http://127.0.0.1:5000/api/grants',
    'http://127.0.0.1:5000/api/team-members',
    'http://127.0.0.1:5000/api/tasks'
]

for url in endpoints:
    print(f"\nFetching {url}...")
    try:
        res = session.get(url, timeout=10)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"Success: Received data length: {len(data)}")
        else:
            print(f"Error: {res.text}")
    except Exception as e:
        print(f"Exception for {url}: {e}")
