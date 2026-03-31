# /tmp/check_roles.py
import sqlite3
import os

db_path = 'e:/Post-Award-Grant-Management-System-MUBAS (PAGMS)/pagms-mubas/backend/instance/app.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT role FROM user")
    roles = cursor.fetchall()
    print("User roles in database:", roles)
    conn.close()
else:
    print("Database not found at", db_path)
