
import sqlite3
import os

db_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\pagms.db'

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Checking 'grants' table for ethics columns...")
    cursor.execute("PRAGMA table_info(grants)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = [
        ("ethics_required", "BOOLEAN DEFAULT 0"),
        ("ethics_status", "VARCHAR(30) DEFAULT 'NOT_SUBMITTED'"),
        ("ethics_expiry_date", "DATE"),
        ("ethics_approval_number", "VARCHAR(100)")
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to 'grants' table...")
            try:
                cursor.execute(f"ALTER TABLE grants ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    print("Checking for 'ethics_suspension_periods' table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ethics_suspension_periods'")
    if not cursor.fetchone():
        print("Creating table 'ethics_suspension_periods'...")
        cursor.execute("""
            CREATE TABLE ethics_suspension_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grant_id INTEGER NOT NULL,
                suspended_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reinstated_at DATETIME,
                suspension_reason VARCHAR(255),
                document_id INTEGER,
                FOREIGN KEY (grant_id) REFERENCES grants (id),
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
    else:
        print("Table 'ethics_suspension_periods' already exists.")
        
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
