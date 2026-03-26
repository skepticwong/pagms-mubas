import os
import sqlite3

def diag_and_migrate():
    base_dir = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas"
    db_paths = [
        os.path.join(base_dir, "backend", "instance", "pagms.db"),
        os.path.join(base_dir, "backend", "instance", "grants.db")
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"DB not found: {db_path}")
            continue
            
        print(f"\nChecking DB: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='milestones'")
        if not cursor.fetchone():
            print("No milestones table in this DB.")
            conn.close()
            continue
            
        # Check columns
        cursor.execute("PRAGMA table_info(milestones)")
        cols = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {cols}")
        
        # Migrate if missing
        missing_cols = [
            ("sequence", "INTEGER DEFAULT 1"),
            ("triggers_tranche", "INTEGER")
        ]
        
        for col_name, col_def in missing_cols:
            if col_name not in cols:
                try:
                    cursor.execute(f"ALTER TABLE milestones ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    print(f"Successfully added {col_name} to {db_path}")
                except Exception as e:
                    print(f"Failed to add {col_name} to {db_path}: {e}")
            else:
                print(f"Column {col_name} already exists.")
        
        conn.close()

if __name__ == "__main__":
    diag_and_migrate()
