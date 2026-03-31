# test_disbursement_unified.py
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

def login_as_finance():
    session = requests.Session()
    # Assuming user 4 is Finance (from previous context or typical seed)
    # We'll try to login or use a known session if possible.
    # For simplicity in this environment, we'll assume we need to login.
    res = session.post(f"{BASE_URL}/login", json={
        "email": "finance@mubas.ac.mw", # Check your seed data
        "password": "password123"
    })
    return session

def login_as_pi():
    session = requests.Session()
    res = session.post(f"{BASE_URL}/login", json={
        "email": "pi@mubas.ac.mw",
        "password": "password123"
    })
    return session

def test_single_payment():
    print("\n--- Testing Single Payment Model ---")
    pi_session = login_as_pi()
    
    # Create a grant with single payment
    grant_data = {
        "title": "Single Payment Test Grant",
        "funder": "Test Funder",
        "grant_code": f"SP-{datetime.now().strftime('%H%M%S')}",
        "start_date": "2024-03-01",
        "end_date": "2025-03-01",
        "total_budget": 100000,
        "currency": "USD",
        "disbursement_type": "single",
        "milestones": []
    }
    
    res = pi_session.post(f"{BASE_URL}/grants", json=grant_data)
    if res.status_code != 201:
        print(f"Failed to create grant: {res.text}")
        return
    
    grant_id = res.json()['grant_id']
    print(f"Created Grant ID: {grant_id}")
    
    # Check Finance Dashboard
    fin_session = login_as_finance()
    dash = fin_session.get(f"{BASE_URL}/finance/dashboard").json()
    
    queue = dash.get('disbursementQueue', [])
    found = [item for item in queue if item.get('grant_id') == grant_id and item.get('type') == 'single']
    
    if found:
        print(f"Success: Grant found in disbursement queue: {found[0]['stage']}")
        # Release it
        rel = fin_session.post(f"{BASE_URL}/finance/release-disbursement", json={
            "grant_id": grant_id,
            "type": "single"
        })
        print(f"Release Result: {rel.status_code} - {rel.json().get('message')}")
    else:
        print("Error: Grant not found in disbursement queue")

def test_milestone_disbursement():
    print("\n--- Testing Milestone-Based Disbursement ---")
    pi_session = login_as_pi()
    
    # Create a grant with milestone-based disbursement
    grant_data = {
        "title": "Milestone Test Grant",
        "funder": "Test Funder",
        "grant_code": f"MB-{datetime.now().strftime('%H%M%S')}",
        "start_date": "2024-03-01",
        "end_date": "2025-03-01",
        "total_budget": 50000,
        "currency": "USD",
        "disbursement_type": "milestone_based",
        "milestones": [
            {
                "title": "Phase 1: Setup",
                "description": "Initial setup",
                "due_date": "2024-04-01",
                "funding_amount": 20000
            }
        ]
    }
    
    res = pi_session.post(f"{BASE_URL}/grants", json=grant_data)
    grant_id = res.json()['grant_id']
    print(f"Created Grant ID: {grant_id}")
    
    # Get the milestone ID
    m_res = pi_session.get(f"{BASE_URL}/grants/{grant_id}/milestones").json()
    m_id = m_res[0]['id']
    print(f"Milestone ID: {m_id}")
    
    # Complete the milestone (simulated)
    # Typically this involves tasks, but we'll try to update status directly if allowed for testing or create a task
    # For this test, we assume a helper or direct DB update if possible, 
    # but let's try the proper way: Create a task and complete it.
    task_data = {
        "grant_id": grant_id,
        "milestone_id": m_id,
        "title": "Test Task",
        "assigned_to": 1, # PI themselves
        "estimated_hours": 10,
        "deadline": "2024-03-31"
    }
    pi_session.post(f"{BASE_URL}/tasks", json=task_data)
    
    # We need to find the task ID...
    tasks = pi_session.get(f"{BASE_URL}/tasks").json()['tasks']
    t_id = [t['id'] for t in tasks if t['grant_id'] == grant_id][0]
    
    # Complete task
    pi_session.put(f"{BASE_URL}/tasks/{t_id}/status", json={"status": "COMPLETED"})
    # Milestone might auto-complete if tasks are done? 
    # Let's check milestone status. 
    # Typically in this system, the PI marks milestone as complete manually in the UI or it auto-completes.
    # Looking at Milestone model, it has status.
    
    # Mark milestone as COMPLETED
    pi_session.put(f"{BASE_URL}/milestones/{m_id}", json={
        "title": "Phase 1: Setup",
        "due_date": "2024-04-01",
        "status": "COMPLETED"
    })
    
    # Check Finance Dashboard
    fin_session = login_as_finance()
    dash = fin_session.get(f"{BASE_URL}/finance/dashboard").json()
    
    queue = dash.get('disbursementQueue', [])
    found = [item for item in queue if item.get('milestone_id') == m_id]
    
    if found:
        print(f"Success: Milestone found in disbursement queue: {found[0]['stage']}")
        # Release it
        rel = fin_session.post(f"{BASE_URL}/finance/release-disbursement", json={
            "grant_id": grant_id,
            "type": "milestone",
            "item_id": m_id
        })
        print(f"Release Result: {rel.status_code} - {rel.json().get('message')}")
    else:
        print("Error: Milestone not found in disbursement queue")

if __name__ == "__main__":
    test_single_payment()
    test_milestone_disbursement()
