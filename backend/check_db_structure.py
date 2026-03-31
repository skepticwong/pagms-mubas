#!/usr/bin/env python3
import sqlite3
import os

# Path to database
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'pagms.db')

print(f"Checking database at: {db_path}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check grants table structure
    print("\n=== GRANTS TABLE STRUCTURE ===")
    cursor.execute("PRAGMA table_info(grants)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    # Check if we have grants data
    print("\n=== GRANTS DATA ===")
    cursor.execute("SELECT COUNT(*) FROM grants")
    count = cursor.fetchone()[0]
    print(f"Total grants: {count}")
    
    if count > 0:
        cursor.execute("SELECT title, start_date, end_date, total_budget FROM grants LIMIT 3")
        grants = cursor.fetchall()
        print("\nSample grants:")
        for grant in grants:
            print(f"  Title: {grant[0]}")
            print(f"  Start: {grant[1]}")
            print(f"  End: {grant[2]}")
            print(f"  Budget: {grant[3]}")
            print()
    
    conn.close()
else:
    print("Database file not found!")
    print(f"Expected at: {db_path}")
