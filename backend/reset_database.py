#!/usr/bin/env python3
"""
Complete database reset and recreation script
"""

import os
import shutil
import sqlite3

def reset_database():
    """Completely reset and recreate the database"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(backend_dir, 'instance')
    db_path = os.path.join(instance_dir, 'pagms.db')
    
    print("🔄 Starting complete database reset...")
    
    # 1. Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed existing database: {db_path}")
    
    # 2. Remove instance directory if it exists
    if os.path.exists(instance_dir):
        shutil.rmtree(instance_dir)
        print(f"✅ Removed instance directory: {instance_dir}")
    
    # 3. Create fresh database using SQLAlchemy
    print("🔧 Creating fresh database with correct schema...")
    
    # Import and create app
    import sys
    sys.path.insert(0, backend_dir)
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from models import db
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Verify schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check grants table
        cursor.execute('PRAGMA table_info(grants)')
        columns = cursor.fetchall()
        print("\n📋 Grants table schema:")
        has_funder_id = False
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            if col[1] == 'funder_id':
                has_funder_id = True
        
        if has_funder_id:
            print("✅ funder_id column exists")
        else:
            print("❌ funder_id column missing")
            return False
        
        # Check funder_profiles table
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="funder_profiles"')
        funder_table = cursor.fetchone()
        if funder_table:
            print("✅ funder_profiles table exists")
        else:
            print("❌ funder_profiles table missing")
            return False
        
        conn.close()
        
        # 4. Run seed data
        print("\n🌱 Adding seed data...")
        try:
            # Import and run seed script
            exec(open('seed_sql.py').read())
            print("✅ Seed data added successfully")
        except Exception as e:
            print(f"⚠️  Seed data warning: {e}")
        
        # 5. Verify data
        from models import User, Grant, FunderProfile
        
        users_count = User.query.count()
        grants_count = Grant.query.count()
        funders_count = FunderProfile.query.count()
        
        print(f"\n📊 Database verification:")
        print(f"  - Users: {users_count}")
        print(f"  - Grants: {grants_count}")
        print(f"  - Funders: {funders_count}")
        
        if users_count > 0 and grants_count > 0 and funders_count > 0:
            print("✅ Database reset completed successfully!")
            return True
        else:
            print("❌ Database reset incomplete")
            return False

if __name__ == '__main__':
    success = reset_database()
    if not success:
        exit(1)
