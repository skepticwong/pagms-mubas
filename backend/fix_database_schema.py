import sqlite3
import os

def fix_database_schema():
    db_path = os.path.join('instance', 'pagms.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current grants table structure
    cursor.execute('PRAGMA table_info(grants)')
    columns = cursor.fetchall()
    print('Current grants table columns:')
    has_funder_id = False
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
        if col[1] == 'funder_id':
            has_funder_id = True

    if not has_funder_id:
        print('\nAdding funder_id column...')
        cursor.execute('ALTER TABLE grants ADD COLUMN funder_id INTEGER')
        conn.commit()
        print('Added funder_id column')

    # Check funder_profiles table
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="funder_profiles"')
    funder_exists = cursor.fetchone()
    if not funder_exists:
        print('\nCreating funder_profiles table...')
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
                ('National Institutes of Health', 'grants@nih.gov', 'Monthly progress reports, annual financial reports', 'NIH Compliance'),
                ('Private Foundation', 'contact@foundation.org', 'Annual reports, financial statements', 'Standard Compliance')
        ''')
        conn.commit()
        print('Created funder_profiles table with default data')
    else:
        cursor.execute('SELECT COUNT(*) FROM funder_profiles')
        count = cursor.fetchone()[0]
        print(f'funder_profiles table exists with {count} records')

    conn.close()
    print('Database schema verification complete')

if __name__ == '__main__':
    fix_database_schema()
