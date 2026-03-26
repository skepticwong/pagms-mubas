import requests
import json
import os

BASE_URL = "http://localhost:5000/api"

def test_milestones():
    # 1. Login
    session = requests.Session()
    login_res = session.post(f"{BASE_URL}/login", json={
        "email": "pi@mubas.ac.mw",
        "password": "mubas123"
    })
    if login_res.status_code != 200:
        print("Login failed")
        return

    print("Logged in as PI.")

    # 2. Get a grant ID
    grants_res = session.get(f"{BASE_URL}/grants")
    grants = grants_res.json()
    if not grants:
        print("No grants found for test.")
        return
    
    grant_id = grants[0]['id']
    print(f"Using grant ID: {grant_id}")

    # 3. Create a milestone
    ms_data = {
        "grant_id": grant_id,
        "title": "Verification Phase 1",
        "description": "Test milestone creation",
        "due_date": "2026-12-31",
        "reporting_period": "Q4 2026",
        "triggers_tranche": 2
    }
    create_res = session.post(f"{BASE_URL}/milestones", json=ms_data)
    if create_res.status_code != 201:
        print(f"Failed to create milestone: {create_res.text}")
        return
    
    milestone = create_res.json()
    ms_id = milestone['id']
    print(f"Created milestone with ID: {ms_id}")
    print(f"Sequence: {milestone.get('sequence')}, Triggers Tranche: {milestone.get('triggers_tranche')}")

    # 4. Create another milestone (test sequencing)
    ms_data_2 = ms_data.copy()
    ms_data_2["title"] = "Verification Phase 2"
    create_res_2 = session.post(f"{BASE_URL}/milestones", json=ms_data_2)
    milestone_2 = create_res_2.json()
    print(f"Created second milestone. Sequence: {milestone_2.get('sequence')}")

    # 5. Test reordering
    reorder_res = session.post(f"{BASE_URL}/grants/{grant_id}/milestones/reorder", json={
        "ordered_ids": [milestone_2['id'], milestone['id']]
    })
    if reorder_res.status_code == 200:
        reordered = reorder_res.json()
        print(f"Reorder successful. New order: {[m['title'] for m in reordered]}")
    else:
        print(f"Reorder failed: {reorder_res.text}")

    # 6. Test deletion constraint
    # Create a task for milestone 1
    task_data = {
        "grant_id": grant_id,
        "assigned_to": 2, # team@mubas.ac.mw
        "milestone_id": ms_id,
        "title": "Test Task",
        "task_type": "Research",
        "deadline": "2026-11-30"
    }
    # Need to check if there's a task create endpoint
    # Actually, I'll just skip the task creation and test simple deletion first
    del_res = session.delete(f"{BASE_URL}/milestones/{ms_id}")
    if del_res.status_code == 200:
        print("Deleted milestone successfully (no tasks case).")
    else:
        print(f"Failed to delete milestone: {del_res.text}")

    # Clean up second milestone
    session.delete(f"{BASE_URL}/milestones/{milestone_2['id']}")

if __name__ == "__main__":
    test_milestones()
