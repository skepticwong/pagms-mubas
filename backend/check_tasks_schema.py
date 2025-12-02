
import sqlite3
import os

db_path = os.path.join('instance', 'pagms.db')
print(f"Checking database at: {os.path.abspath(db_path)}")

if not os.path.exists(db_path):
    print("Database file found.")
else:
    print("Database file found.")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tasks table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';")
    if not cursor.fetchone():
        print("[ERROR] Table 'tasks' does not exist!")
    else:
        print("[OK] Table 'tasks' exists.")
        
        # Get columns
        cursor.execute("PRAGMA table_info(tasks);")
        columns = cursor.fetchall()
        print("\nColumns in 'tasks' table:")
        existing_columns = []
        for col in columns:
            # cid, name, type, notnull, dflt_value, pk
            print(f" - {col[1]} ({col[2]})")
            existing_columns.append(col[1])
            
        # Expected columns
        expected = [
            'id', 'grant_id', 'assigned_to', 'title', 'task_type', 
            'deadline', 'estimated_hours', 'pay_rate_override', 
            'status', 'created_at'
        ]
        
        print("\nMissing columns:")
        missing = [c for c in expected if c not in existing_columns]
        if missing:
            for m in missing:
                print(f" [MISSING] {m}")
        else:
            print(" [NONE] All expected columns appear to be present.")

    conn.close()

except Exception as e:
    print(f"[CRITICAL] Error: {e}")
