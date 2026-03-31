import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

def verify_effort():
    session = requests.Session()
    
    # 1. Login as PI
    print("--- 1. Login as PI ---")
    login_res = session.post(f"{BASE_URL}/login", json={
        "email": "pi@mubas.ac.mw",
        "password": "mubas123"
    })
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
    print("PI Logged in.")

    # 2. Get Grant
    print("\n--- 2. Fetching Grants ---")
    grants_res = session.get(f"{BASE_URL}/grants")
    grants = grants_res.json().get('grants', [])
    if not grants:
        print("No grants found.")
        return
    grant_id = grants[0]['id']
    print(f"Using Grant ID: {grant_id}")

    # 3. Check Effort Status
    print("\n--- 3. Checking Effort Status ---")
    status_res = session.get(f"{BASE_URL}/effort/status/{grant_id}")
    status = status_res.json()
    print(f"Is Locked: {status.get('is_locked')}")
    print(f"Message: {status.get('message')}")
    print(f"Severity: {status.get('severity')}")

    # 4. Check Pending Effort
    print("\n--- 4. Checking Pending Effort ---")
    pending_res = session.get(f"{BASE_URL}/effort/pending/{grant_id}")
    pending = pending_res.json()
    print(f"Period: {pending['period']['month_name']} {pending['period']['year']}")
    print(f"Total Records: {len(pending['effort_records'])}")
    
    # 5. Test "Team First" Rule (Attempt PI cert when team is pending)
    # Note: This depends on the DB state. If team is already certified, this might succeed.
    print("\n--- 5. Testing 'Team First' Rule ---")
    cert_data = {
        "grant_id": grant_id,
        "year": pending['period']['year'],
        "month": pending['period']['month'],
        "percentage": 50.0,
        "signature": "PI Signature"
    }
    cert_res = session.post(f"{BASE_URL}/effort/certify", json=cert_data)
    if cert_res.status_code == 400:
        print(f"Blocked as expected: {cert_res.json().get('error')}")
    else:
        print(f"Result: {cert_res.status_code}")
        print(f"Body: {cert_res.text}")

    # 6. Test Enforcement Gate (Expense Block)
    # We need to be past day 10 for a real lock, but EffortService.check_spending_lock uses current date.
    # If today < 10, it will return 'warn'.
    print("\n--- 6. Testing Expense Submission Gate ---")
    expense_data = {
        "grant_id": grant_id,
        "category": "Travel",
        "description": "Verification Test Expense",
        "amount": 100.0,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    expense_res = session.post(f"{BASE_URL}/expenses/submit", json=expense_data)
    if expense_res.status_code == 403:
        print(f"Expense blocked by effort lock: {expense_res.json().get('error')}")
    elif expense_res.status_code == 201:
        print("Expense permitted (Status likely 'warn' or 'safe' based on date/certs).")
    else:
        print(f"Expense status: {expense_res.status_code}")
        print(f"Response: {expense_res.text}")

    # 7. RSU Override Test
    print("\n--- 7. Testing RSU Override ---")
    # Login as RSU
    session_rsu = requests.Session()
    login_rsu = session_rsu.post(f"{BASE_URL}/login", json={
        "email": "rsu@mubas.ac.mw",
        "password": "mubas123"
    })
    
    override_data = {
        "grant_id": grant_id,
        "year": pending['period']['year'],
        "month": pending['period']['month'],
        "justification": "Verification Override for Lock Testing"
    }
    override_res = session_rsu.post(f"{BASE_URL}/effort/override", json=override_data)
    if override_res.status_code == 200:
        print("RSU Override successful.")
        
        # Verify expense now works (if it was blocked before)
        print("Retesting expense submission after override...")
        expense_res_2 = session.post(f"{BASE_URL}/expenses/submit", json=expense_data)
        if expense_res_2.status_code == 201:
            print("Expense now permitted after override!")
        else:
            print(f"Still failing: {expense_res_2.status_code}")
    else:
        print(f"Override failed: {override_res.status_code} - {override_res.text}")

if __name__ == "__main__":
    verify_effort()
