#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import sqlite3
from backend.app import create_app
from backend.models import db, User

def check_database():
    # Check if database file exists
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'instance', 'grant_management.db')
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        table_exists = cursor.fetchone()
        print(f"Users table exists: {bool(table_exists)}")
        
        if table_exists:
            # Count users
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"Total users: {user_count}")
            
            # List users
            cursor.execute("SELECT id, name, email, role FROM users")
            users = cursor.fetchall()
            for user in users:
                print(f"  ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}")
        
        conn.close()
    
    # Try to initialize with Flask app
    print("\nTrying to initialize with Flask app...")
    try:
        app = create_app()
        with app.app_context():
            db.create_all()
            print("Database tables created/verified")
            
            # Check users through ORM
            users = User.query.all()
            print(f"Users found via ORM: {len(users)}")
            for user in users:
                print(f"  {user.name} ({user.email}) - {user.role}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database()
