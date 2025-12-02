import os
import sqlite3

def patch_db():
    db_path = os.path.join('instance', 'pagms.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prepend 'documents/' to paths that don't have a slash
    cursor.execute("SELECT id, file_path FROM documents")
    rows = cursor.fetchall()
    
    count = 0
    for row_id, file_path in rows:
        if '/' not in file_path and '\\' not in file_path:
            new_path = f"documents/{file_path}"
            cursor.execute("UPDATE documents SET file_path = ? WHERE id = ?", (new_path, row_id))
            count += 1
            print(f"Patched record {row_id}: {file_path} -> {new_path}")
            
    conn.commit()
    conn.close()
    print(f"Finished. Patched {count} records.")

if __name__ == "__main__":
    patch_db()
