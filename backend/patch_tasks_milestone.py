import sqlite3
import os

def patch_database():
    db_path = os.path.join('instance', 'pagms.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add milestone_id column to tasks table
        print("Adding milestone_id column to tasks table...")
        cursor.execute("ALTER TABLE tasks ADD COLUMN milestone_id INTEGER REFERENCES milestones(id)")
        print("Column added successfully.")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column milestone_id already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_database()
