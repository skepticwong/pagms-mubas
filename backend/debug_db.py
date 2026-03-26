
import sqlite3
import os

# Identify DB path correctly
db_path = 'instance/pagms.db'
if not os.path.exists(db_path):
    db_path = 'backend/instance/pagms.db'
if not os.path.exists(db_path):
    db_path = 'pagms.db'

print(f"Checking DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM rules")
    print(f"Rules count: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT id, name FROM rules")
    for r in cursor.fetchall():
        print(f" - Rule {r[0]}: {r[1]}")
        
    cursor.execute("SELECT COUNT(*) FROM rule_profiles")
    print(f"Profiles count: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT id, name, funder_id FROM rule_profiles")
    for p in cursor.fetchall():
        print(f" - Profile {p[0]}: {p[1]} (Funder: {p[2]})")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
