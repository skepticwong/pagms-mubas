import sqlite3
import os

db_path = os.path.join('backend', 'instance', 'pagms.db')
print(f"Checking database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(effort_certifications)")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
