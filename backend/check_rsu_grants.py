
import requests
import json

# 1. Login as RSU
session = requests.Session()
# Assuming RSU credentials based on previous context/seeds
login_payload = {'email': 'rsu@mubas.ac.mw', 'password': 'mubas123'}
print(f"Logging in as {login_payload['email']}...")
login_res = session.post('http://localhost:5000/api/login', json=login_payload)
print(f"Login Status: {login_res.status_code}")
if login_res.status_code != 200:
    print("Login Response:", login_res.text)
    # Try creating the user if not exists (fallback)
    # This assumes the auth bypass or seeder works, but let's stick to standard flow
    exit(1)

# 2. Fetch Grants
print("Fetching /api/grants as RSU...")
res = session.get('http://localhost:5000/api/grants')
print(f"Fetch Status: {res.status_code}")

if res.status_code == 200:
    grants = res.json()
    print(f"Found {len(grants)} grants.")
    for g in grants:
        print(f"- {g.get('title')} (Budget: {g.get('total_budget')})")
else:
    print("Fetch Response:", res.text)
