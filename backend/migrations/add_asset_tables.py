"""
Add Asset & Equipment Management tables
Migration script for Asset, AssetMaintenance, and AssetTransfer tables
"""

import sqlite3
import os
from datetime import datetime

def upgrade():
    """Create asset management tables"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'pagms.db')
    
    if not os.path.exists(db_path):
        print("Database not found. Please run the application first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating asset management tables...")
        
        # Create assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_tag VARCHAR(50) UNIQUE,
                serial_number VARCHAR(100),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                grant_id INTEGER NOT NULL,
                source_type VARCHAR(20) NOT NULL,
                owner_name VARCHAR(200),
                lending_agreement TEXT,
                purchase_cost FLOAT DEFAULT 0.0,
                linked_expense_id INTEGER,
                rental_fee_total FLOAT DEFAULT 0.0,
                depreciation_value FLOAT DEFAULT 0.0,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                custodian_user_id INTEGER,
                assigned_task_id INTEGER,
                acquisition_date DATE,
                expected_return_date DATE,
                actual_return_date DATE,
                last_maintenance_date DATE,
                next_maintenance_date DATE,
                disposition_method VARCHAR(50),
                disposition_approved_by INTEGER,
                disposition_date DATE,
                disposition_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by_user_id INTEGER,
                supporting_documents TEXT,
                FOREIGN KEY (grant_id) REFERENCES grants (id),
                FOREIGN KEY (custodian_user_id) REFERENCES users (id),
                FOREIGN KEY (assigned_task_id) REFERENCES tasks (id),
                FOREIGN KEY (disposition_approved_by) REFERENCES users (id),
                FOREIGN KEY (created_by_user_id) REFERENCES users (id)
            )
        ''')
        
        # Create asset_maintenance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                maintenance_type VARCHAR(50),
                description TEXT,
                cost FLOAT DEFAULT 0.0,
                performed_by VARCHAR(200),
                performed_date DATE,
                next_due_date DATE,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by_user_id INTEGER,
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE,
                FOREIGN KEY (created_by_user_id) REFERENCES users (id)
            )
        ''')
        
        # Create asset_transfers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                from_user_id INTEGER,
                to_user_id INTEGER,
                transfer_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                approved_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id),
                FOREIGN KEY (approved_by) REFERENCES users (id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_grant_id ON assets (grant_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_status ON assets (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_custodian ON assets (custodian_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_source_type ON assets (source_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset_maintenance_asset_id ON asset_maintenance (asset_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset_transfers_asset_id ON asset_transfers (asset_id)')
        
        conn.commit()
        print("✅ Asset management tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def downgrade():
    """Remove asset management tables"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'pagms.db')
    
    if not os.path.exists(db_path):
        print("Database not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Removing asset management tables...")
        
        # Drop tables in reverse order of creation (due to foreign keys)
        cursor.execute('DROP TABLE IF EXISTS asset_transfers')
        cursor.execute('DROP TABLE IF EXISTS asset_maintenance')
        cursor.execute('DROP TABLE IF EXISTS assets')
        
        conn.commit()
        print("✅ Asset management tables removed successfully!")
        
    except Exception as e:
        print(f"❌ Error removing tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def verify():
    """Verify that tables were created correctly"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'pagms.db')
    
    if not os.path.exists(db_path):
        print("Database not found.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['assets', 'asset_maintenance', 'asset_transfers']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check table structures
        for table in required_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"✅ Table {table} has {len(columns)} columns")
        
        print("✅ All asset management tables verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("Asset Management Tables Migration")
    print("=" * 40)
    
    try:
        upgrade()
        verify()
        print("\n🎉 Migration completed successfully!")
        print("\nYou can now:")
        print("1. Start the backend: python app.py")
        print("2. Access Asset Management from the frontend")
        print("3. Create and manage assets for your grants")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check the error above and try again.")
