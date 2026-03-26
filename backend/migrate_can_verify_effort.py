import sqlite3
import os
import sys

def migrate():
    # Database path relative to this script
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'pagms.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    print(f"Connected to database: {db_path}")
    
    try:
        # We use raw sqlite3 to avoid SQLAlchemy metadata caching issues
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check and add grant_team.can_verify_effort
        cursor.execute("PRAGMA table_info(grant_team)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'can_verify_effort' not in columns:
            cursor.execute("ALTER TABLE grant_team ADD COLUMN can_verify_effort BOOLEAN DEFAULT 0")
            print("  [SUCCESS] grant_team.can_verify_effort column added")
        else:
            print("  [WARNING] grant_team.can_verify_effort already exists — skipping")

        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
