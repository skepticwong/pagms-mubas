import sqlite3
import os
import shutil

def fix_funder_id_column():
    """Directly fix the missing funder_id column"""
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(backend_dir, 'instance', 'pagms.db')
    
    print("🔧 Fixing funder_id column issue...")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current grants table structure
        cursor.execute('PRAGMA table_info(grants)')
        columns = cursor.fetchall()
        
        print("Current grants table columns:")
        has_funder_id = False
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            if col[1] == 'funder_id':
                has_funder_id = True
        
        if not has_funder_id:
            print("\nAdding funder_id column...")
            cursor.execute('ALTER TABLE grants ADD COLUMN funder_id INTEGER')
            conn.commit()
            print("✅ Added funder_id column")
            
            # Verify it was added
            cursor.execute('PRAGMA table_info(grants)')
            columns = cursor.fetchall()
            print("\nUpdated grants table columns:")
            for col in columns:
                if col[1] == 'funder_id':
                    print(f"  ✅ {col[1]} ({col[2]})")
        else:
            print("\n✅ funder_id column already exists")
        
        # Check if funder_profiles table exists
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="funder_profiles"')
        funder_table = cursor.fetchone()
        
        if not funder_table:
            print("\nCreating funder_profiles table...")
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
            
            # Add default funders
            cursor.execute('''
                INSERT INTO funder_profiles (name, contact_email, reporting_requirements, compliance_framework)
                VALUES 
                    ('National Science Foundation', 'grants@nsf.gov', 'Quarterly reports, annual financial statements', 'NSF Compliance'),
                    ('Private Foundation', 'contact@foundation.org', 'Annual reports, financial statements', 'Standard Compliance'),
                    ('National Institutes of Health', 'grants@nih.gov', 'Monthly progress reports, annual financial reports', 'NIH Compliance')
            ''')
            
            conn.commit()
            print("✅ Created funder_profiles table with default data")
            
            # Update existing grants to have funder_id = 1
            cursor.execute('UPDATE grants SET funder_id = 1 WHERE funder_id IS NULL')
            conn.commit()
            print("✅ Updated existing grants with funder_id")
        else:
            cursor.execute('SELECT COUNT(*) FROM funder_profiles')
            count = cursor.fetchone()[0]
            print(f"\n✅ funder_profiles table exists with {count} records")
        
        print("\n🎉 Database schema fixed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error fixing database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = fix_funder_id_column()
    if not success:
        exit(1)
