
import sqlite3
import os

try:
    db_path = os.path.join('instance', 'pagms.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tasks)")
    cols = [c[1] for c in cursor.fetchall()]
    
    with open('db_cols.txt', 'w') as f:
        f.write(','.join(cols))
    conn.close()
    print("Verification complete.")
except Exception as e:
    with open('db_cols.txt', 'w') as f:
        f.write(f"ERROR: {e}")
