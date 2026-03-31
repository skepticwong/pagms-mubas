"""
Migration script to add NCE, Burn Rate, and Forecasting tables
Run with: python migrations/add_nce_burn_forecast_tables.py
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db, GrantAmendment, GrantFinancialMetrics
from app import create_app

def upgrade():
    """Create the new tables for NCE, Burn Rate, and Forecasting"""
    app = create_app()
    
    with app.app_context():
        print("Creating GrantAmendment table...")
        
        # Create GrantAmendment table
        GrantAmendment.__table__.create(db.engine, checkfirst=True)
        print("✅ GrantAmendment table created successfully")
        
        print("Creating GrantFinancialMetrics table...")
        
        # Create GrantFinancialMetrics table
        GrantFinancialMetrics.__table__.create(db.engine, checkfirst=True)
        print("✅ GrantFinancialMetrics table created successfully")
        
        # Create indexes for performance
        print("Creating indexes...")
        
        # Indexes for GrantAmendment
        db.execute("CREATE INDEX IF NOT EXISTS idx_amendments_grant_id ON grant_amendments(grant_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_amendments_status ON grant_amendments(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_amendments_type ON grant_amendments(amendment_type)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_amendments_requested_at ON grant_amendments(requested_at)")
        
        # Indexes for GrantFinancialMetrics
        db.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_grant_id ON grant_financial_metrics(grant_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_burn_status ON grant_financial_metrics(burn_rate_status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_forecast_status ON grant_financial_metrics(forecast_status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_last_calculated ON grant_financial_metrics(last_calculated)")
        
        print("✅ Indexes created successfully")
        
        # Commit the changes
        db.session.commit()
        print("🎉 Migration completed successfully!")

def downgrade():
    """Remove the new tables (for rollback)"""
    app = create_app()
    
    with app.app_context():
        print("Dropping indexes...")
        
        # Drop indexes
        db.execute("DROP INDEX IF EXISTS idx_amendments_grant_id")
        db.execute("DROP INDEX IF EXISTS idx_amendments_status")
        db.execute("DROP INDEX IF EXISTS idx_amendments_type")
        db.execute("DROP INDEX IF EXISTS idx_amendments_requested_at")
        db.execute("DROP INDEX IF EXISTS idx_financial_metrics_grant_id")
        db.execute("DROP INDEX IF EXISTS idx_financial_metrics_burn_status")
        db.execute("DROP INDEX IF EXISTS idx_financial_metrics_forecast_status")
        db.execute("DROP INDEX IF EXISTS idx_financial_metrics_last_calculated")
        
        print("Dropping tables...")
        
        # Drop tables
        GrantFinancialMetrics.__table__.drop(db.engine, checkfirst=True)
        GrantAmendment.__table__.drop(db.engine, checkfirst=True)
        
        print("✅ Tables dropped successfully")
        
        # Commit the changes
        db.session.commit()
        print("🔄 Rollback completed successfully!")

def verify():
    """Verify that the tables were created correctly"""
    app = create_app()
    
    with app.app_context():
        print("Verifying table creation...")
        
        # Check GrantAmendment table
        try:
            result = db.execute("SELECT COUNT(*) FROM grant_amendments")
            count = result.scalar()
            print(f"✅ GrantAmendment table exists (contains {count} rows)")
        except Exception as e:
            print(f"❌ GrantAmendment table error: {e}")
            return False
        
        # Check GrantFinancialMetrics table
        try:
            result = db.execute("SELECT COUNT(*) FROM grant_financial_metrics")
            count = result.scalar()
            print(f"✅ GrantFinancialMetrics table exists (contains {count} rows)")
        except Exception as e:
            print(f"❌ GrantFinancialMetrics table error: {e}")
            return False
        
        # Check indexes
        print("Verifying indexes...")
        indexes = [
            'idx_amendments_grant_id',
            'idx_amendments_status', 
            'idx_amendments_type',
            'idx_financial_metrics_grant_id',
            'idx_financial_metrics_burn_status',
            'idx_financial_metrics_forecast_status'
        ]
        
        for index_name in indexes:
            try:
                result = db.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
                exists = result.fetchone()
                if exists:
                    print(f"✅ Index {index_name} exists")
                else:
                    print(f"⚠️  Index {index_name} not found")
            except Exception as e:
                print(f"❌ Error checking index {index_name}: {e}")
        
        print("🎉 Verification completed!")
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration for NCE, Burn Rate, and Forecasting tables')
    parser.add_argument('action', choices=['upgrade', 'downgrade', 'verify'], 
                       help='Action to perform: upgrade (create), downgrade (remove), or verify')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        upgrade()
    elif args.action == 'downgrade':
        downgrade()
    elif args.action == 'verify':
        verify()
    else:
        print("Invalid action. Use 'upgrade', 'downgrade', or 'verify'.")
