
import sqlite3
import os

# Find the database file. Usually in 'instance/' or backend root.
db_path = 'instance/pagms.db'
if not os.path.exists(db_path):
    db_path = 'pagms.db'

print(f"DEBUG: Checking database at {db_path}")

if not os.path.exists(db_path):
    print("ERROR: Database file not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT COUNT(*) FROM rules")
    rules_count = cursor.fetchone()[0]
    print(f"Rules count: {rules_count}")
    
    cursor.execute("SELECT name, funder_id FROM rule_profiles")
    profiles = cursor.fetchall()
    print(f"Profiles found: {len(profiles)}")
    for p in profiles:
        print(f" - {p[0]} (Funder: {p[1]})")
except Exception as e:
    print(f"Error querying DB: {e}")

conn.close()
