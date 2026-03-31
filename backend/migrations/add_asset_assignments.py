# migrations/add_asset_assignments.py
"""
Migration script to add AssetAssignment model and update existing relationships
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, AssetAssignment
from sqlalchemy import text

def upgrade():
    """Create the asset_assignments table and set up indexes"""
    
    print("🔄 Starting AssetAssignment migration...")
    
    try:
        # Create the asset_assignments table
        print("📋 Creating asset_assignments table...")
        AssetAssignment.__table__.create(db.engine)
        print("✅ AssetAssignment table created successfully")
        
        # Create indexes for better performance
        print("🔍 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_asset_assignments_task ON asset_assignments(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_asset_assignments_asset ON asset_assignments(asset_id)",
            "CREATE INDEX IF NOT EXISTS idx_asset_assignments_user ON asset_assignments(assigned_to_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_asset_assignments_status ON asset_assignments(status)",
            "CREATE INDEX IF NOT EXISTS idx_asset_assignments_created_at ON asset_assignments(requested_at)"
        ]
        
        for index_sql in indexes:
            try:
                db.session.execute(text(index_sql))
                print(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"⚠️  Index creation warning: {e}")
        
        db.session.commit()
        print("🎉 AssetAssignment migration completed successfully!")
        
        # Print table info
        print("\n📊 AssetAssignment Table Structure:")
        print("- id (Primary Key)")
        print("- task_id (Foreign Key -> tasks.id)")
        print("- asset_id (Foreign Key -> assets.id)")
        print("- status (REQUESTED | ASSIGNED | RETURNED)")
        print("- requested_at, assigned_at, returned_at (Timestamps)")
        print("- assigned_to_user_id (Foreign Key -> users.id)")
        print("- pickup_confirmed_by, return_confirmed_by (Foreign Keys -> users.id)")
        print("- pickup_evidence_doc, return_evidence_doc (File paths)")
        print("- notes (Text)")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.session.rollback()
        raise

def downgrade():
    """Remove the asset_assignments table (for rollback)"""
    
    print("🔄 Rolling back AssetAssignment migration...")
    
    try:
        # Drop the table
        AssetAssignment.__table__.drop(db.engine)
        print("✅ AssetAssignment table dropped successfully")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        raise

if __name__ == "__main__":
    # This allows running the migration directly
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        upgrade()
