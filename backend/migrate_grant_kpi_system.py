#!/usr/bin/env python3
"""
Migration Script: Add Grant KPI System
Creates grant_kpis table and updates milestone_kpis table for Phase 1 implementation
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from datetime import datetime

def migrate_grant_kpi_system():
    """Create grant-level KPI system tables"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting Grant KPI System Migration...")
        print("=" * 60)
        
        try:
            # 1. Create grant_kpis table
            print("📋 Creating grant_kpis table...")
            db.engine.execute("""
                CREATE TABLE IF NOT EXISTS grant_kpis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grant_id INTEGER NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    unit VARCHAR(50),
                    category VARCHAR(50),
                    grant_wide_target FLOAT NOT NULL,
                    baseline_value FLOAT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by_user_id INTEGER,
                    FOREIGN KEY (grant_id) REFERENCES grants (id),
                    FOREIGN KEY (created_by_user_id) REFERENCES users (id)
                )
            """)
            print("✅ grant_kpis table created successfully")
            
            # 2. Add new columns to milestone_kpis table
            print("📋 Updating milestone_kpis table...")
            
            # Check if grant_kpi_id column exists
            result = db.engine.execute("""
                PRAGMA table_info(milestone_kpis)
            """).fetchall()
            
            columns = [row[1] for row in result]
            
            if 'grant_kpi_id' not in columns:
                db.engine.execute("""
                    ALTER TABLE milestone_kpis 
                    ADD COLUMN grant_kpi_id INTEGER
                """)
                print("✅ Added grant_kpi_id column")
            
            if 'milestone_target' not in columns:
                db.engine.execute("""
                    ALTER TABLE milestone_kpis 
                    ADD COLUMN milestone_target FLOAT
                """)
                print("✅ Added milestone_target column")
            
            # 3. Create indexes for performance
            print("📋 Creating indexes...")
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_grant_kpis_grant_id 
                ON grant_kpis(grant_id)
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_milestone_kpis_grant_kpi_id 
                ON milestone_kpis(grant_kpi_id)
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_milestone_kpis_milestone_grant_kpi 
                ON milestone_kpis(milestone_id, grant_kpi_id)
            """)
            
            print("✅ Indexes created successfully")
            
            # 4. Migrate existing milestone KPIs to grant KPIs
            print("📋 Migrating existing milestone KPIs...")
            
            # Get existing milestone KPIs that don't have grant_kpi_id
            existing_kpis = db.engine.execute("""
                SELECT DISTINCT name, unit 
                FROM milestone_kpis 
                WHERE grant_kpi_id IS NULL
            """).fetchall()
            
            migrated_count = 0
            for kpi_name, kpi_unit in existing_kpis:
                # Create a grant KPI for each unique KPI name
                # We'll need to assign it to a grant - for now, use the first grant
                first_grant = db.engine.execute("""
                    SELECT id FROM grants LIMIT 1
                """).fetchone()
                
                if first_grant:
                    grant_id = first_grant[0]
                    
                    # Check if grant KPI already exists
                    existing_grant_kpi = db.engine.execute("""
                        SELECT id FROM grant_kpis 
                        WHERE grant_id = ? AND name = ?
                    """, (grant_id, kpi_name)).fetchone()
                    
                    if not existing_grant_kpi:
                        # Create grant KPI
                        db.engine.execute("""
                            INSERT INTO grant_kpis 
                            (grant_id, name, unit, category, grant_wide_target, created_by_user_id)
                            VALUES (?, ?, ?, 'legacy', 999999, 1)
                        """, (grant_id, kpi_name, kpi_unit or 'count'))
                        
                        grant_kpi_id = db.engine.execute("""
                            SELECT last_insert_rowid()
                        """).fetchone()[0]
                        
                        # Update all milestone KPIs with this name
                        db.engine.execute("""
                            UPDATE milestone_kpis 
                            SET grant_kpi_id = ?, milestone_target = target_value
                            WHERE name = ? AND grant_kpi_id IS NULL
                        """, (grant_kpi_id, kpi_name))
                        
                        migrated_count += 1
                        print(f"   ✅ Migrated KPI: {kpi_name}")
            
            print(f"✅ Migration completed. {migrated_count} KPIs migrated")
            
            # 5. Add sample grant KPIs for testing
            print("📋 Adding sample grant KPIs...")
            
            # Get first grant for testing
            test_grant = db.engine.execute("""
                SELECT id FROM grants LIMIT 1
            """).fetchone()
            
            if test_grant:
                grant_id = test_grant[0]
                
                sample_kpis = [
                    {
                        'name': 'Publications',
                        'description': 'Research papers published in peer-reviewed journals',
                        'unit': 'papers',
                        'category': 'research',
                        'grant_wide_target': 10
                    },
                    {
                        'name': 'Students Trained',
                        'description': 'Graduate students supervised and trained',
                        'unit': 'students',
                        'category': 'training',
                        'grant_wide_target': 5
                    },
                    {
                        'name': 'Workshops Conducted',
                        'description': 'Training workshops and seminars delivered',
                        'unit': 'sessions',
                        'category': 'training',
                        'grant_wide_target': 3
                    },
                    {
                        'name': 'Equipment Procured',
                        'description': 'Research equipment and instruments purchased',
                        'unit': 'items',
                        'category': 'infrastructure',
                        'grant_wide_target': 2
                    },
                    {
                        'name': 'Beneficiaries Reached',
                        'description': 'People directly impacted by the project',
                        'unit': 'people',
                        'category': 'community',
                        'grant_wide_target': 100
                    }
                ]
                
                for kpi_data in sample_kpis:
                    # Check if already exists
                    existing = db.engine.execute("""
                        SELECT id FROM grant_kpis 
                        WHERE grant_id = ? AND name = ?
                    """, (grant_id, kpi_data['name'])).fetchone()
                    
                    if not existing:
                        db.engine.execute("""
                            INSERT INTO grant_kpis 
                            (grant_id, name, description, unit, category, grant_wide_target, created_by_user_id)
                            VALUES (?, ?, ?, ?, ?, ?, 1)
                        """, (grant_id, kpi_data['name'], kpi_data['description'], 
                              kpi_data['unit'], kpi_data['category'], kpi_data['grant_wide_target']))
                        
                        print(f"   ✅ Added sample KPI: {kpi_data['name']}")
            
            print("✅ Sample KPIs added successfully")
            
            print("=" * 60)
            print("🎉 Grant KPI System Migration Complete!")
            print("📊 Tables created: grant_kpis")
            print("📊 Tables updated: milestone_kpis")
            print("📊 Indexes created for performance")
            print("📊 Sample data added for testing")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = migrate_grant_kpi_system()
    if success:
        print("\n✅ Migration completed successfully!")
        print("🚀 Grant KPI System is ready for Phase 1 implementation!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
