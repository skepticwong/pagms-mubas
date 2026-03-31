"""
Test script to verify NCE, Burn Rate, and Forecasting models are working correctly
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from models import db, GrantAmendment, GrantFinancialMetrics, Grant, User
from app import create_app

def test_models():
    """Test that the new models work correctly"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing NCE, Burn Rate, and Forecasting models...")
        
        try:
            # Test GrantAmendment model
            print("\n1. Testing GrantAmendment model...")
            
            # Create a test amendment
            test_amendment = GrantAmendment(
                grant_id=1,  # Assuming grant with ID 1 exists
                amendment_type='NCE',
                title='Test Extension Request',
                description='Test description',
                current_end_date='2024-12-31',
                requested_new_end_date='2025-03-31',
                extension_days=90,
                justification='Test justification for extension',
                requested_by=1  # Assuming user with ID 1 exists
            )
            
            print("✅ GrantAmendment model creation successful")
            print(f"   - Amendment Type: {test_amendment.amendment_type}")
            print(f"   - Extension Days: {test_amendment.extension_days}")
            print(f"   - Status: {test_amendment.status}")
            
            # Test to_dict method
            amendment_dict = test_amendment.to_dict()
            print("✅ GrantAmendment.to_dict() method works")
            print(f"   - Keys: {list(amendment_dict.keys())}")
            
        except Exception as e:
            print(f"❌ GrantAmendment model error: {e}")
            return False
        
        try:
            # Test GrantFinancialMetrics model
            print("\n2. Testing GrantFinancialMetrics model...")
            
            # Create test metrics
            test_metrics = GrantFinancialMetrics(
                grant_id=1,  # Assuming grant with ID 1 exists
                time_elapsed_percentage=45.5,
                budget_spent_percentage=60.2,
                burn_rate_variance=14.7,
                burn_rate_status='OVER_SPENDING',
                projected_final_spend=95000.00,
                projected_remaining_balance=5000.00,
                forecast_status='TIGHT',
                risk_score=75.5,
                risk_factors=['HIGH_PENDING_EXPENSES', 'TIME_PRESSURE']
            )
            
            print("✅ GrantFinancialMetrics model creation successful")
            print(f"   - Burn Rate Status: {test_metrics.burn_rate_status}")
            print(f"   - Variance: {test_metrics.burn_rate_variance}%")
            print(f"   - Forecast Status: {test_metrics.forecast_status}")
            
            # Test to_dict method
            metrics_dict = test_metrics.to_dict()
            print("✅ GrantFinancialMetrics.to_dict() method works")
            print(f"   - Keys: {list(metrics_dict.keys())}")
            
        except Exception as e:
            print(f"❌ GrantFinancialMetrics model error: {e}")
            return False
        
        try:
            # Test database operations
            print("\n3. Testing database operations...")
            
            # Check if we can query the tables
            amendments_count = db.session.query(GrantAmendment).count()
            metrics_count = db.session.query(GrantFinancialMetrics).count()
            
            print(f"✅ Database queries successful")
            print(f"   - GrantAmendments in DB: {amendments_count}")
            print(f"   - GrantFinancialMetrics in DB: {metrics_count}")
            
        except Exception as e:
            print(f"❌ Database operations error: {e}")
            return False
        
        try:
            # Test model relationships
            print("\n4. Testing model relationships...")
            
            # Get a sample grant to test relationships
            sample_grant = db.session.query(Grant).first()
            if sample_grant:
                print(f"✅ Found sample grant: {sample_grant.title}")
                
                # Test amendments relationship
                print(f"   - Amendments relationship exists: {hasattr(sample_grant, 'amendments')}")
                print(f"   - Financial metrics relationship exists: {hasattr(sample_grant, 'financial_metrics')}")
                
            else:
                print("⚠️  No grants found in database (relationships not tested)")
            
        except Exception as e:
            print(f"❌ Model relationships error: {e}")
            return False
        
        print("\n🎉 All tests passed! Phase 1 implementation is working correctly.")
        return True

def check_table_structure():
    """Check the actual table structure in the database"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Checking table structure...")
        
        try:
            # Check GrantAmendment table structure
            result = db.execute("PRAGMA table_info(grant_amendments)")
            columns = result.fetchall()
            
            print("\nGrantAmendment table columns:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # Check GrantFinancialMetrics table structure
            result = db.execute("PRAGMA table_info(grant_financial_metrics)")
            columns = result.fetchall()
            
            print("\nGrantFinancialMetrics table columns:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
                
        except Exception as e:
            print(f"❌ Table structure check error: {e}")
            return False
        
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1: NCE, BURN RATE & FORECASTING MODELS TEST")
    print("=" * 60)
    
    # Run tests
    success = test_models()
    
    if success:
        check_table_structure()
        print("\n✅ Phase 1 completed successfully!")
        print("📋 Ready to proceed to Phase 2: Backend Services")
    else:
        print("\n❌ Phase 1 failed! Please fix the errors before proceeding.")
