import requests
import json
import os

BASE_URL = "http://localhost:5000/api"

def verify_report_flow():
    # 1. Login
    session = requests.Session()
    login_data = {
        "email": "pi@mubas.ac.mw",
        "password": "password123"
    }
    print("Testing login...")
    res = session.post(f"{BASE_URL}/login", json=login_data)
    if res.status_code != 200:
        print("Login failed")
        return

    # 2. Get Grants
    print("Fetching grants...")
    res = session.get(f"{BASE_URL}/grants")
    grants = res.json()
    if not grants:
        print("No grants found for user")
        return
    
    grant_id = grants[0]['id']
    grant_code = grants[0]['grant_code']
    print(f"Using Grant: {grant_code} (ID: {grant_id})")

    # 3. Get Reporting Options
    print("Fetching reporting options...")
    res = session.get(f"{BASE_URL}/grants/{grant_id}/reporting-options")
    options = res.json()
    print(f"Options found: {json.dumps(options, indent=2)}")
    
    if not options:
        print("No reporting options found. (This might be expected for a very new grant)")
        # Create a fake option to test generation if needed, but we'll try to use a real one
        return

    # 4. Generate Report
    selected_option = options[0]
    print(f"Generating report: {selected_option['label']}...")
    res = session.post(f"{BASE_URL}/grants/{grant_id}/generate-report", json={
        "type": selected_option['type'],
        "value": selected_option['value']
    })
    
    if res.status_code == 200:
        result = res.json()
        print("Report generated successfully!")
        print(f"Download URL: {result['download_url']}")
        print(f"Preview URL: {result['preview_url']}")
    else:
        print(f"Failed to generate report: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    verify_report_flow()
