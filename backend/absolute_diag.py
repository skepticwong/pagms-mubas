
import sqlite3
import os

db_path = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\instance\pagms.db"
log_path = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\final_diag.txt"

def log(msg):
    with open(log_path, 'a') as f:
        f.write(msg + '\n')

def main():
    if os.path.exists(log_path):
        os.remove(log_path)
    
    if not os.path.exists(db_path):
        log(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(expense_claims)")
    cols = [c[1] for c in cursor.fetchall()]
    log(f"Columns: {cols}")
    conn.close()

if __name__ == "__main__":
    main()
