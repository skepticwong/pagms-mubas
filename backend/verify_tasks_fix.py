
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_task_flow():
    session = requests.Session()
    
    # 1. Login as PI
    print("\n--- 1. Login as PI ---")
    login_res = session.post(f"{BASE_URL}/login", json={
        "email": "pi@mubas.ac.mw",
        "password": "mubas123"
    })
    print(f"Login Status: {login_res.status_code}")
    if login_res.status_code != 200:
        print("Login failed. Make sure the backend is running.")
        return

    # 2. Get Grants and Team Members (need IDs for task creation)
    print("\n--- 2. Fetching Grants and Team Members ---")
    grants_res = session.get(f"{BASE_URL}/grants")
    team_res = session.get(f"{BASE_URL}/team-members")
    
    grants = grants_res.json()
    team_members = team_res.json().get('team_members', [])
    
    if not grants or not team_members:
        print("Required data missing. Ensure grants and team members exist.")
        return
        
    grant_id = grants[0]['id']
    assigned_to_id = team_members[0]['id']
    
    print(f"Using Grant ID: {grant_id}, Assignee ID: {assigned_to_id}")

    # 3. Create Task
    print("\n--- 3. Creating Task ---")
    task_payload = {
        "grant_id": grant_id,
        "assigned_to": assigned_to_id,
        "title": "Verification Task",
        "task_type": "Fieldwork",
        "deadline": "2026-12-31",
        "estimated_hours": 10
    }
    create_res = session.post(f"{BASE_URL}/tasks", json=task_payload)
    print(f"Create Status: {create_res.status_code}")
    task = create_res.json()
    print(f"Properties: {list(task.keys())}")
    
    # Check for expected properties
    expected_props = ['assigned_to_name', 'assigned_to_email', 'grant_code', 'grant_title']
    for prop in expected_props:
        if prop in task:
            print(f" [OK] Found {prop}: {task[prop]}")
        else:
            print(f" [FAIL] Missing {prop}")

    task_id = task['id']

    # 4. Get Tasks
    print("\n--- 4. Getting Tasks ---")
    tasks_res = session.get(f"{BASE_URL}/tasks")
    tasks = tasks_res.json().get('tasks', [])
    found = False
    for t in tasks:
        if t['id'] == task_id:
            found = True
            print(f"Found created task in list.")
            for prop in expected_props:
                if prop in t:
                    print(f" [OK] Prop {prop} present in list.")
                else:
                    print(f" [FAIL] Prop {prop} missing in list.")
    if not found:
        print("[FAIL] Task not found in list.")

    # 5. Update Task
    print("\n--- 5. Updating Task ---")
    update_payload = {"title": "Updated Verification Task"}
    update_res = session.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
    print(f"Update Status: {update_res.status_code}")
    if update_res.status_code == 200:
        updated_task = update_res.json()
        print(f"Updated Title: {updated_task['title']}")
        if updated_task['title'] == update_payload['title']:
            print("[OK] Update successful.")
        else:
            print("[FAIL] Title mismatch after update.")
    else:
        print(f"[FAIL] Update failed: {update_res.text}")

    # 6. Delete Task
    print("\n--- 6. Deleting Task ---")
    delete_res = session.delete(f"{BASE_URL}/tasks/{task_id}")
    print(f"Delete Status: {delete_res.status_code}")
    if delete_res.status_code == 200:
        print("[OK] Deletion successful.")
    else:
        print("[FAIL] Deletion failed.")

if __name__ == "__main__":
    test_task_flow()
