
import sqlite3
import os

db_path = os.path.join('instance', 'pagms.db')
print(f"Connecting to database at: {os.path.abspath(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of columns that might be missing
    columns_to_add = [
        ("task_type", "TEXT"),
        ("estimated_hours", "REAL"),
        ("pay_rate_override", "REAL"),
        ("status", "TEXT DEFAULT 'assigned'"),
        ("created_at", "DATETIME")
    ]

    print("Checking and patching 'tasks' table...")
    
    # Check if table exists first
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';")
    if not cursor.fetchone():
        print("[WARNING] Table 'tasks' does not exist! Creating it...")
        cursor.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                grant_id INTEGER NOT NULL,
                assigned_to INTEGER NOT NULL,
                title TEXT NOT NULL,
                task_type TEXT NOT NULL,
                deadline DATE NOT NULL,
                estimated_hours REAL,
                pay_rate_override REAL,
                status TEXT DEFAULT 'assigned',
                created_at DATETIME,
                FOREIGN KEY(grant_id) REFERENCES grants(id),
                FOREIGN KEY(assigned_to) REFERENCES users(id)
            )
        """)
        print("[OK] Created 'tasks' table.")
    else:
        for col, dtype in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col} {dtype}")
                print(f"[OK] Added column: {col}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e):
                    print(f"[INFO] Column {col} already exists. Skipped.")
                else:
                    print(f"[ERROR] Error adding {col}: {e}")

    conn.commit()
    conn.close()
    print("\nTasks table patch completed successfully!")

except Exception as e:
    print(f"\n[CRITICAL] Error patching database: {e}")
