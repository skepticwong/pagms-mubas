#!/usr/bin/env python3
"""
Database migration script to add missing funder_id column and funder_profiles table
"""

import sqlite3
import os
import sys

def migrate_database():
    """Add missing database schema elements"""
    db_path = os.path.join('instance', 'pagms.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # 1. Add funder_id column to grants table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE grants ADD COLUMN funder_id INTEGER')
            print("✅ Added funder_id column to grants table")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print("✅ funder_id column already exists in grants table")
            else:
                raise e
        
        # 2. Create funder_profiles table if it doesn't exist
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="funder_profiles"')
        if not cursor.fetchone():
            print("Creating funder_profiles table...")
            cursor.execute('''
                CREATE TABLE funder_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    contact_email VARCHAR(100),
                    reporting_requirements TEXT,
                    compliance_framework VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Created funder_profiles table")
            
            # Add some default funder profiles
            cursor.execute('''
                INSERT INTO funder_profiles (name, contact_email, reporting_requirements, compliance_framework)
                VALUES 
                    ('National Science Foundation', 'grants@nsf.gov', 'Quarterly reports, annual financial statements', 'NSF Compliance'),
                    ('National Institutes of Health', 'grants@nih.gov', 'Monthly progress reports, annual financial reports', 'NIH Compliance'),
                    ('Private Foundation', 'contact@foundation.org', 'Annual reports, financial statements', 'Standard Compliance'),
                    ('International Funder', 'grants@intl.org', 'Bi-annual reports, audit requirements', 'International Standards')
            ''')
            print("✅ Added default funder profiles")
        else:
            print("✅ funder_profiles table already exists")
        
        # 3. Update existing grants to have a default funder_id if they don't have one
        cursor.execute('SELECT COUNT(*) FROM grants WHERE funder_id IS NULL')
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"Updating {null_count} grants with default funder_id...")
            cursor.execute('UPDATE grants SET funder_id = 1 WHERE funder_id IS NULL')
            print("✅ Updated grants with default funder_id")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
        # Verify the changes
        cursor.execute('PRAGMA table_info(grants)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Grants table columns: {columns}")
        
        cursor.execute('SELECT COUNT(*) FROM funder_profiles')
        funder_count = cursor.fetchone()[0]
        print(f"Funder profiles count: {funder_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
