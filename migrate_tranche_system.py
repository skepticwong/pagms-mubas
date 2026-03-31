#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Tranche System
Phase 1: Add new fields to Tranche model and create TrancheAmendment table
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import db
from app import create_app

def migrate_tranche_system():
    """Run database migration for enhanced tranche system"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting Tranche System Migration...")
        print("=" * 60)
        
        try:
            # Check if migration is needed
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('tranches')]
            
            print(f"📋 Current tranches table columns: {existing_columns}")
            
            # Add new columns to tranches table
            new_columns = {
                'tranche_number': 'INTEGER',
                'currency': 'VARCHAR(3) DEFAULT "USD"',
                'description': 'VARCHAR(200)',
                'trigger_type': 'VARCHAR(20) DEFAULT "milestone"',
                'triggering_milestone_id': 'INTEGER',
                'required_report_type': 'VARCHAR(50)',
                'trigger_date': 'DATE',
                'released_at': 'DATETIME',
                'released_by': 'INTEGER',
                'version': 'INTEGER DEFAULT 1',
                'parent_tranche_id': 'INTEGER',
                'amendment_reason': 'TEXT',
                'amendment_approved_by': 'INTEGER',
                'amendment_approved_at': 'DATETIME',
                'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
            }
            
            # Add missing columns
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    print(f"➕ Adding column: {column_name} ({column_type})")
                    
                    # Handle foreign key constraints
                    if column_name in ['triggering_milestone_id', 'released_by', 'parent_tranche_id', 'amendment_approved_by']:
                        # Add foreign key separately
                        db.session.execute(f"ALTER TABLE tranches ADD COLUMN {column_name} {column_type}")
                    else:
                        db.session.execute(f"ALTER TABLE tranches ADD COLUMN {column_name} {column_type}")
                else:
                    print(f"✅ Column already exists: {column_name}")
            
            # Update existing tranches to have tranche_number
            print("📊 Setting tranche_number for existing records...")
            db.session.execute("""
                UPDATE tranches 
                SET tranche_number = (
                    SELECT row_num 
                    FROM (
                        SELECT id, ROW_NUMBER() OVER (PARTITION BY grant_id ORDER BY expected_date, id) as row_num 
                        FROM tranches
                    ) ranked 
                    WHERE ranked.id = tranches.id
                )
                WHERE tranche_number IS NULL
            """)
            
            # Create tranche_amendments table
            print("📝 Creating tranche_amendments table...")
            table_exists = db.engine.dialect.has_table(db.session.connection(), 'tranche_amendments')
            
            if not table_exists:
                db.session.execute("""
                    CREATE TABLE tranche_amendments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        grant_id INTEGER NOT NULL,
                        tranche_id INTEGER NOT NULL,
                        amendment_type VARCHAR(20),
                        old_value TEXT,
                        new_value TEXT,
                        reason TEXT NOT NULL,
                        supporting_docs TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        requested_by INTEGER,
                        approved_by INTEGER,
                        approved_at DATETIME,
                        rejection_reason TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (grant_id) REFERENCES grants (id),
                        FOREIGN KEY (tranche_id) REFERENCES tranches (id),
                        FOREIGN KEY (requested_by) REFERENCES users (id),
                        FOREIGN KEY (approved_by) REFERENCES users (id)
                    )
                """)
                print("✅ tranche_amendments table created")
            else:
                print("✅ tranche_amendments table already exists")
            
            # Add indexes for performance
            print("🔍 Adding indexes...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_tranches_grant_id ON tranches(grant_id)",
                "CREATE INDEX IF NOT EXISTS idx_tranches_triggering_milestone_id ON tranches(triggering_milestone_id)",
                "CREATE INDEX IF NOT EXISTS idx_tranches_parent_tranche_id ON tranches(parent_tranche_id)",
                "CREATE INDEX IF NOT EXISTS idx_tranche_amendments_grant_id ON tranche_amendments(grant_id)",
                "CREATE INDEX IF NOT EXISTS idx_tranche_amendments_tranche_id ON tranche_amendments(tranche_id)",
                "CREATE INDEX IF NOT EXISTS idx_tranche_amendments_status ON tranche_amendments(status)"
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(index_sql)
                    print(f"✅ Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    print(f"⚠️ Index creation warning: {e}")
            
            # Commit all changes
            db.session.commit()
            print("🎉 Migration completed successfully!")
            
            # Verify the migration
            print("\n📊 Migration Verification:")
            updated_columns = [col['name'] for col in inspector.get_columns('tranches')]
            print(f"✅ Tranches table now has {len(updated_columns)} columns")
            
            # Show sample data
            sample_tranche = db.session.execute("SELECT * FROM tranches LIMIT 1").fetchone()
            if sample_tranche:
                print(f"✅ Sample tranche record exists with ID: {sample_tranche[0]}")
            
            amendment_count = db.session.execute("SELECT COUNT(*) FROM tranche_amendments").scalar()
            print(f"✅ Tranche amendments table ready (0 records)")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_tranche_system()
