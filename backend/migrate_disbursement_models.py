
import sqlite3
import os

db_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\instance\pagms.db'

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Adding disbursement_type to grants table...")
        cursor.execute("ALTER TABLE grants ADD COLUMN disbursement_type VARCHAR(20) DEFAULT 'tranches'")
    except sqlite3.OperationalError:
        print("disbursement_type already exists in grants table.")

    try:
        print("Adding funding fields to milestones table...")
        cursor.execute("ALTER TABLE milestones ADD COLUMN funding_amount FLOAT DEFAULT 0.0")
        cursor.execute("ALTER TABLE milestones ADD COLUMN release_status VARCHAR(20) DEFAULT 'pending'")
    except sqlite3.OperationalError:
        print("Funding fields already exist in milestones table.")

    print("Creating tranches table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tranches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grant_id INTEGER NOT NULL,
        amount FLOAT NOT NULL,
        expected_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        actual_received_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grant_id) REFERENCES grants(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
