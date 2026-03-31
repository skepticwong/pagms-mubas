# Simple check for grants in database
import sqlite3
import os

db_file = os.path.join('backend', 'instance', 'pagms.db')

if os.path.exists(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check grants
        cursor.execute("SELECT COUNT(*) FROM grants")
        count = cursor.fetchone()[0]
        print(f"Grants in database: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, grant_code, title, status FROM grants LIMIT 5")
            grants = cursor.fetchall()
            for g in grants:
                print(f"  - {g[0]}: {g[1]} - {g[2]} ({g[3]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file not found: {db_file}")
