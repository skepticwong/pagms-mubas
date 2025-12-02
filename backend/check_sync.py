import os
import sqlite3

def check_sync():
    db_path = os.path.join('instance', 'pagms.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, file_name, file_path, doc_type FROM documents ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    
    print(f"{'ID':<5} | {'Type':<20} | {'Path':<50}")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]:<5} | {row[3]:<20} | {row[2]:<50}")
            
    conn.close()

if __name__ == "__main__":
    check_sync()
