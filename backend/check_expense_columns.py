
import sqlite3
import os

db_path = os.path.join('instance', 'pagms.db')

def check_columns():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(expense_claims)")
        columns = cursor.fetchall()
        print("\nColumns in expense_claims:")
        for col in columns:
            print(f" - {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_columns()
