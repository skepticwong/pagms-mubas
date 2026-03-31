import sqlite3
import os

db_path = 'instance/pagms.db'
if not os.path.exists(db_path):
    print(f"DB NOT FOUND AT {db_path}")
    # Try current dir
    db_path = 'pagms.db'

conn = sqlite3.connect(db_path)
c = conn.cursor()

print(f"Using DB: {os.path.abspath(db_path)}")

# 1. Get Users
print("\n--- USERS ---")
c.execute("SELECT id, name, email, role FROM users")
users = c.fetchall()
for u in users:
    print(f"ID: {u[0]}, Name: {u[1]}, Email: {u[2]}, Role: {u[3]}")

# 2. Get Grants
print("\n--- GRANTS ---")
c.execute("SELECT id, grant_code, title, pi_id, status FROM grants")
grants = c.fetchall()
for g in grants:
    print(f"ID: {g[0]}, Code: {g[1]}, Title: {g[2]}, PI_ID: {g[3]}, Status: {g[4]}")

# 3. Get Team
print("\n--- GRANT TEAM ---")
try:
    c.execute("SELECT grant_id, user_id, role FROM grant_team")
    team = c.fetchall()
    for t in team:
        print(f"GrantID: {t[0]}, UserID: {t[1]}, Role: {t[2]}")
except Exception as e:
    print(f"GrantTeam error: {e}")

conn.close()
