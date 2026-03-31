import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_milestone_crud():
    # 1. Login (assuming we have a test user or session)
    # Since we can't easily handle sessions here without cookies, 
    # we'll assume the environment might need manual session setup or we mock it.
    # However, for a simple check, we'll try to GET milestones for grant 1.
    
    grant_id = 1
    
    print(f"--- Testing Milestones for Grant {grant_id} ---")
    
    # We'll use a session to keep cookies
    session = requests.Session()
    
    # Login
    login_url = f"{BASE_URL}/login"
    login_data = {"email": "pi@mubas.ac.mw", "password": "mubas123"} # Mock credentials
    try:
        res = session.post(login_url, json=login_data)
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            # return
    except Exception as e:
        print(f"Login error: {e}")

    # 1. GET Milestones
    try:
        res = session.get(f"{BASE_URL}/grants/{grant_id}/milestones")
        print(f"GET milestones: {res.status_code}")
        if res.status_code == 200:
            print(f"Data: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"GET error: {e}")

    # 2. POST Milestone
    new_milestone = {
        "grant_id": grant_id,
        "title": "Verification Milestone",
        "due_date": "2026-12-31",
        "description": "Created by verification script"
    }
    try:
        res = session.post(f"{BASE_URL}/milestones", json=new_milestone)
        print(f"POST milestone: {res.status_code}")
        if res.status_code == 201:
            m_id = res.json()['id']
            print(f"Created milestone with ID: {m_id}")
            
            # 3. PUT Milestone
            update_data = {"title": "Updated Verification Milestone"}
            res = session.put(f"{BASE_URL}/milestones/{m_id}", json=update_data)
            print(f"PUT milestone: {res.status_code}")
            
            # 4. DELETE Milestone
            res = session.delete(f"{BASE_URL}/milestones/{m_id}")
            print(f"DELETE milestone: {res.status_code}")
    except Exception as e:
        print(f"POST error: {e}")

if __name__ == "__main__":
    test_milestone_crud()
