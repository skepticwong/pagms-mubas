import sqlite3
import os

db_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\instance\pagms.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type_def):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in cursor.fetchall()]
    if column not in cols:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            print(f"Added {table}.{column}")
        except Exception as e:
            print(f"Error adding {table}.{column}: {e}")
    else:
        print(f"Column {table}.{column} already exists")

add_column('documents', 'source_type', "VARCHAR(20) DEFAULT 'GENERIC'")
add_column('documents', 'expense_id', "INTEGER")
add_column('deliverables_submissions', 'external_links', "TEXT")
add_column('deliverables_submissions', 'expense_id', "INTEGER")

conn.commit()
conn.close()
print("Migration completed.")
