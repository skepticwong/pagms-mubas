
import sqlite3
import os

db_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\instance\pagms.db'

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables found:")
    for t in tables:
        print(f" - {t}")
    conn.close()
