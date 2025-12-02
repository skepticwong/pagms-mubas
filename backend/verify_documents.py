import requests
import json
import os
import time

BASE_URL = "http://localhost:5000/api"

def test_documents():
    # 1. Login
    session = requests.Session()
    try:
        login_res = session.post(f"{BASE_URL}/login", json={
            "email": "pi@mubas.ac.mw",
            "password": "mubas123"
        })
        print(f"Login: {login_res.status_code}")
        if login_res.status_code != 200:
            print("Login failed")
            return
    except Exception as e:
        print(f"Connection error: {e}")
        return

    # 2. Get Grants
    grants_res = session.get(f"{BASE_URL}/grants")
    grants = grants_res.json()
    if not grants:
        print("No grants found")
        return
    grant_id = grants[0]['id']
    print(f"Testing with Grant ID: {grant_id}")

    # 3. Upload Document v1
    file_path = "test_doc_v1.txt"
    with open(file_path, "w") as f:
        f.write("This is version 1 content")

    try:
        with open(file_path, "rb") as f:
            upload_res = session.post(f"{BASE_URL}/documents/upload", data={
                "grant_id": grant_id,
                "doc_type": "Award Letter"
            }, files={"file": f})
        print(f"Upload v1: {upload_res.status_code}")
        print(upload_res.json())
        
        if upload_res.status_code != 201:
            print("Upload v1 failed")
            return
            
        doc_v1_id = upload_res.json()['id']
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # 4. Upload Document v2 (same type)
    time.sleep(1) # Ensure different timestamp if needed
    file_path_v2 = "test_doc_v2.txt"
    with open(file_path_v2, "w") as f:
        f.write("This is version 2 content - Updated")

    try:
        with open(file_path_v2, "rb") as f:
            upload_res2 = session.post(f"{BASE_URL}/documents/upload", data={
                "grant_id": grant_id,
                "doc_type": "Award Letter"
            }, files={"file": f})
        print(f"Upload v2: {upload_res2.status_code}")
        print(upload_res2.json())
    finally:
        if os.path.exists(file_path_v2):
            os.remove(file_path_v2)

    # 5. List Documents and Verify Versioning
    docs_res = session.get(f"{BASE_URL}/documents", params={"grant_id": grant_id})
    docs = docs_res.json()
    print(f"Total documents: {len(docs)}")
    
    found_v1 = False
    found_v2 = False
    
    for doc in docs:
        print(f"ID: {doc['id']}, Name: {doc['file_name']}, Version: {doc['version']}, Superseded: {doc['is_superseded']}")
        if doc['version'] == 1:
            found_v1 = True
            if not doc['is_superseded']:
                print("FAILED: Version 1 should be superseded")
        if doc['version'] == 2:
            found_v2 = True
            if doc['is_superseded']:
                print("FAILED: Version 2 should NOT be superseded")
                
    if found_v1 and found_v2:
        print("SUCCESS: Versioning logic verified")
    else:
        print(f"FAILED: Missing versions. v1: {found_v1}, v2: {found_v2}")

if __name__ == "__main__":
    test_documents()
