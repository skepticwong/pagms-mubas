
import sqlite3
import os

db_path = os.path.join('instance', 'pagms.db')
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM grants")
    grant_count = cursor.fetchone()[0]
    
    print(f"Users: {user_count}")
    print(f"Grants: {grant_count}")
    
    if grant_count > 0:
        cursor.execute("SELECT title, pi_id FROM grants LIMIT 1")
        row = cursor.fetchone()
        print(f"Example Grant: {row[0]} (PI ID: {row[1]})")
    
    cursor.execute("SELECT id, email, role FROM users")
    for row in cursor.fetchall():
        print(f"User: {row[0]}, {row[1]}, {row[2]}")
        
    conn.close()
