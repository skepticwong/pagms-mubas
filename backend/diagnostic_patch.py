
import sqlite3
import os

db_path = os.path.join('instance', 'pagms.db')
log_path = 'db_patch_log.txt'

def log(msg):
    print(msg)
    with open(log_path, 'a') as f:
        f.write(msg + '\n')

def main():
    if os.path.exists(log_path):
        os.remove(log_path)
        
    if not os.path.exists(db_path):
        log(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(expense_claims)")
    columns = [col[1] for col in cursor.fetchall()]
    log(f"Current columns: {columns}")
    
    needed = [
        ("expense_date", "DATE"),
        ("description", "TEXT"),
        ("receipt_filename", "VARCHAR(200)"),
        ("payment_method", "VARCHAR(50)")
    ]
    
    for col_name, col_type in needed:
        if col_name not in columns:
            try:
                log(f"Adding column {col_name}...")
                cursor.execute(f"ALTER TABLE expense_claims ADD COLUMN {col_name} {col_type}")
                log(f"Success.")
            except Exception as e:
                log(f"Error adding {col_name}: {e}")
        else:
            log(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    log("Done.")

if __name__ == "__main__":
    main()
