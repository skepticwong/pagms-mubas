# migrations/add_milestone_kpis_and_templates.py
"""
Migration script to add MilestoneKPI and MilestoneTemplate models
Phase 1: Compliance Core Implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from models import db, MilestoneKPI, MilestoneTemplate
from sqlalchemy import text

def upgrade():
    """Create milestone_kpis and milestone_templates tables"""
    print("🔄 Starting Milestone KPIs and Templates migration...")
    
    # Create milestone_kpis table
    print("📋 Creating milestone_kpis table...")
    db.engine.execute("""
        CREATE TABLE milestone_kpis (
            id INTEGER PRIMARY KEY,
            milestone_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            target_value FLOAT NOT NULL,
            unit VARCHAR(50),
            actual_value FLOAT,
            achievement_pct FLOAT,
            evidence_link VARCHAR(255),
            status VARCHAR(20) DEFAULT 'PENDING',
            FOREIGN KEY (milestone_id) REFERENCES milestones (id)
        )
    """)
    print("✅ milestone_kpis table created successfully")
    
    # Create milestone_templates table
    print("📋 Creating milestone_templates table...")
    db.engine.execute("""
        CREATE TABLE milestone_templates (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            config_json JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by_user_id INTEGER,
            FOREIGN KEY (created_by_user_id) REFERENCES users (id)
        )
    """)
    print("✅ milestone_templates table created successfully")
    
    # Create indexes
    print("🔍 Creating indexes...")
    db.engine.execute("CREATE INDEX idx_milestone_kpis_milestone_id ON milestone_kpis(milestone_id)")
    db.engine.execute("CREATE INDEX idx_milestone_kpis_status ON milestone_kpis(status)")
    db.engine.execute("CREATE INDEX idx_milestone_templates_name ON milestone_templates(name)")
    print("✅ All indexes created successfully")
    
    # Insert basic templates
    print("📦 Inserting basic milestone templates...")
    templates = [
        {
            'name': 'Standard Field Work',
            'config_json': {
                'assets': ['GPS Unit', 'Camera', 'Sampling Kit', 'Safety Equipment'],
                'kpis': [
                    {'name': 'Samples Collected', 'unit': 'Count', 'target': 50},
                    {'name': 'Farmers Interviewed', 'unit': 'Count', 'target': 25},
                    {'name': 'Field Days', 'unit': 'Count', 'target': 5}
                ]
            }
        },
        {
            'name': 'Laboratory Analysis',
            'config_json': {
                'assets': ['Lab Equipment', 'Safety Gear', 'Computer'],
                'kpis': [
                    {'name': 'Samples Analyzed', 'unit': 'Count', 'target': 100},
                    {'name': 'Quality Checks Passed', 'unit': '%', 'target': 95}
                ]
            }
        },
        {
            'name': 'Report Writing',
            'config_json': {
                'assets': ['Computer', 'Printer'],
                'kpis': [
                    {'name': 'Report Sections Completed', 'unit': 'Count', 'target': 8},
                    {'name': 'Review Rounds Completed', 'unit': 'Count', 'target': 3}
                ]
            }
        }
    ]
    
    for template in templates:
        db.engine.execute(f"""
            INSERT INTO milestone_templates (name, config_json)
            VALUES ('{template["name"]}', '{json.dumps(template["config_json"])}')
        """)
    
    print(f"✅ Inserted {len(templates)} basic templates")
    print("🎉 Milestone KPIs and Templates migration completed successfully!")

def downgrade():
    """Rollback the migration"""
    print("🔄 Rolling back Milestone KPIs and Templates migration...")
    
    # Drop tables
    db.engine.execute("DROP TABLE IF EXISTS milestone_kpis")
    db.engine.execute("DROP TABLE IF EXISTS milestone_templates")
    
    print("✅ Migration rollback completed")

if __name__ == "__main__":
    try:
        upgrade()
        print("\n🎊 SUCCESS: Phase 1 database migration completed!")
    except Exception as e:
        print(f"\n❌ ERROR: Migration failed - {str(e)}")
        sys.exit(1)
