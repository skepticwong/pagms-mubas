
import sqlite3
import os

db_path = os.path.join('instance', 'pagms.db')

def patch_database():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        ("expense_date", "DATE"),
        ("description", "TEXT"),
        ("receipt_filename", "VARCHAR(200)"),
        ("payment_method", "VARCHAR(50)")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            print(f"Adding column {col_name} to expense_claims...")
            cursor.execute(f"ALTER TABLE expense_claims ADD COLUMN {col_name} {col_type}")
            print(f"Successfully added {col_name}.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")
                
    conn.commit()
    conn.close()
    print("Database patch complete.")

if __name__ == "__main__":
    patch_database()
