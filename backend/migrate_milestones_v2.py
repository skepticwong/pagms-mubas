import os
import sqlite3

def migrate():
    # Path to the database
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    db_path = os.path.join(instance_path, 'pagms.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print(f"Migrating database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns in milestones
    cursor.execute("PRAGMA table_info(milestones)")
    cols = [col[1] for col in cursor.fetchall()]

    new_cols = [
        ("sequence", "INTEGER DEFAULT 1"),
        ("triggers_tranche", "INTEGER")
    ]

    for col_name, col_def in new_cols:
        if col_name not in cols:
            try:
                cursor.execute(f"ALTER TABLE milestones ADD COLUMN {col_name} {col_def}")
                print(f"Added column {col_name} to milestones table.")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists in milestones table.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
