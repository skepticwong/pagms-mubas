import os
import sqlite3

db_path = os.path.join('instance', 'pagms.db')
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- USERS ---")
cursor.execute("SELECT id, name, email, role FROM users")
users = cursor.fetchall()
for u in users:
    print(u)

print("\n--- GRANTS ---")
cursor.execute("SELECT id, grant_code, title, pi_id FROM grants")
grants = cursor.fetchall()
for g in grants:
    print(g)

print("\n--- GRANT TEAM ---")
cursor.execute("SELECT id, grant_id, user_id, role FROM grant_team")
teams = cursor.fetchall()
for t in teams:
    print(t)

conn.close()
