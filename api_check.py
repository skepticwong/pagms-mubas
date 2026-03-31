import requests
s = requests.Session()
# Try different passwords if needed
pw = 'mubas123'
print(f"Testing login with {pw}...")
r = s.post('http://localhost:5000/api/login', json={'email': 'pi@mubas.ac.mw', 'password': pw})
print(f"Login: {r.status_code}")
if r.status_code != 200:
    pw = 'password123'
    print(f"Testing login with {pw}...")
    r = s.post('http://localhost:5000/api/login', json={'email': 'pi@mubas.ac.mw', 'password': pw})
    print(f"Login: {r.status_code}")

r = s.get('http://localhost:5000/api/grants')
print(f"Grants: {r.status_code}")
if r.status_code == 200:
    grants = r.json()
    print(f"Total grants: {len(grants)}")
    for g in grants:
        if g.get('disbursement_type'):
            print(f"Grant: {g.get('grant_code')} - Type: {g.get('disbursement_type')}")
        else:
            print(f"Grant: {g.get('grant_code')} - Type: MISSING")
