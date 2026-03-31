"""
Simple test to verify the new models are properly defined
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

def test_model_imports():
    """Test that we can import the new models"""
    try:
        from models import GrantAmendment, GrantFinancialMetrics
        print("✅ Successfully imported GrantAmendment and GrantFinancialMetrics")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_attributes():
    """Test that the models have the expected attributes"""
    try:
        from models import GrantAmendment, GrantFinancialMetrics
        
        # Test GrantAmendment attributes
        amendment_attrs = [
            'id', 'grant_id', 'amendment_type', 'title', 'description',
            'current_end_date', 'requested_new_end_date', 'extension_days',
            'status', 'priority', 'justification', 'supporting_docs',
            'requested_by', 'approved_by', 'rejected_by', 'to_dict'
        ]
        
        for attr in amendment_attrs:
            if not hasattr(GrantAmendment, attr):
                print(f"❌ GrantAmendment missing attribute: {attr}")
                return False
        
        print("✅ GrantAmendment has all expected attributes")
        
        # Test GrantFinancialMetrics attributes
        metrics_attrs = [
            'id', 'grant_id', 'time_elapsed_percentage', 'budget_spent_percentage',
            'burn_rate_variance', 'burn_rate_status', 'projected_final_spend',
            'projected_remaining_balance', 'forecast_status', 'risk_score',
            'risk_factors', 'to_dict'
        ]
        
        for attr in metrics_attrs:
            if not hasattr(GrantFinancialMetrics, attr):
                print(f"❌ GrantFinancialMetrics missing attribute: {attr}")
                return False
        
        print("✅ GrantFinancialMetrics has all expected attributes")
        return True
        
    except Exception as e:
        print(f"❌ Attribute test error: {e}")
        return False

def test_model_instantiation():
    """Test that we can create instances of the models"""
    try:
        from models import GrantAmendment, GrantFinancialMetrics
        from datetime import datetime, date
        
        # Test GrantAmendment instantiation
        amendment = GrantAmendment(
            grant_id=1,
            amendment_type='NCE',
            title='Test Extension',
            justification='Test justification',
            requested_by=1
        )
        
        print("✅ GrantAmendment instantiation successful")
        print(f"   - Default status: {amendment.status}")
        print(f"   - Amendment type: {amendment.amendment_type}")
        
        # Test GrantFinancialMetrics instantiation
        metrics = GrantFinancialMetrics(
            grant_id=1,
            time_elapsed_percentage=50.0,
            budget_spent_percentage=60.0,
            burn_rate_variance=10.0
        )
        
        print("✅ GrantFinancialMetrics instantiation successful")
        print(f"   - Default burn status: {metrics.burn_rate_status}")
        print(f"   - Default forecast status: {metrics.forecast_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Instantiation test error: {e}")
        return False

def test_to_dict_methods():
    """Test the to_dict methods"""
    try:
        from models import GrantAmendment, GrantFinancialMetrics
        from datetime import datetime, date
        
        # Test GrantAmendment.to_dict()
        amendment = GrantAmendment(
            grant_id=1,
            amendment_type='NCE',
            title='Test Extension',
            justification='Test justification',
            requested_by=1,
            current_end_date=date(2024, 12, 31),
            requested_new_end_date=date(2025, 3, 31)
        )
        
        amendment_dict = amendment.to_dict()
        expected_keys = ['id', 'grant_id', 'amendment_type', 'title', 'status']
        
        for key in expected_keys:
            if key not in amendment_dict:
                print(f"❌ GrantAmendment.to_dict() missing key: {key}")
                return False
        
        print("✅ GrantAmendment.to_dict() works correctly")
        
        # Test GrantFinancialMetrics.to_dict()
        metrics = GrantFinancialMetrics(
            grant_id=1,
            time_elapsed_percentage=45.5,
            budget_spent_percentage=60.2,
            burn_rate_variance=14.7
        )
        
        metrics_dict = metrics.to_dict()
        expected_keys = ['id', 'grant_id', 'time_elapsed_percentage', 'burn_rate_status']
        
        for key in expected_keys:
            if key not in metrics_dict:
                print(f"❌ GrantFinancialMetrics.to_dict() missing key: {key}")
                return False
        
        print("✅ GrantFinancialMetrics.to_dict() works correctly")
        return True
        
    except Exception as e:
        print(f"❌ to_dict test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1: MODEL DEFINITION TEST")
    print("=" * 60)
    
    tests = [
        test_model_imports,
        test_model_attributes,
        test_model_instantiation,
        test_to_dict_methods
    ]
    
    all_passed = True
    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        if not test():
            all_passed = False
            break
    
    if all_passed:
        print("\n🎉 All model tests passed!")
        print("✅ Phase 1 models are properly defined and ready for database integration")
    else:
        print("\n❌ Some tests failed!")
        print("🔧 Please fix the model definitions before proceeding")
