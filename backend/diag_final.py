
import sqlite3
import os

db_path = 'instance/pagms.db'
if not os.path.exists(db_path):
    db_path = 'pagms.db'

print(f"CHECK: {db_path}")
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM users")
print(f"Users: {cur.fetchone()[0]}")
cur.execute("SELECT name, role FROM users")
for u in cur.fetchall():
    print(f" - {u[0]} ({u[1]})")

cur.execute("SELECT COUNT(*) FROM rules")
rules = cur.fetchone()[0]
print(f"Rules: {rules}")
cur.execute("SELECT name FROM rules")
for r in cur.fetchall():
    print(f" - Rule: {r[0]}")

cur.execute("SELECT COUNT(*) FROM rule_profiles")
profiles = cur.fetchone()[0]
print(f"Profiles: {profiles}")
cur.execute("SELECT name, funder_id FROM rule_profiles")
for p in cur.fetchall():
    print(f" - Profile: {p[0]} ({p[1]})")

conn.close()
