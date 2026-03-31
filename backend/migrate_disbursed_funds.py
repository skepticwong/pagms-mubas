import sys
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from models import db

def migrate():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'pagms.db')
    print(f"Connecting to database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Checking if 'disbursed_funds' column exists in 'grants' table...")
        cursor.execute("PRAGMA table_info(grants)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'disbursed_funds' not in columns:
            print("Adding 'disbursed_funds' column to 'grants' table...")
            cursor.execute("ALTER TABLE grants ADD COLUMN disbursed_funds FLOAT DEFAULT 0.0")
            print("Successfully added 'disbursed_funds' column.")
        else:
            print("'disbursed_funds' column already exists.")
            
        conn.commit()
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
