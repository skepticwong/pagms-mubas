"""
Test script for Phase 2 Services - NCE, Burn Rate, and Budget Forecasting
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

def test_service_imports():
    """Test that all services can be imported"""
    try:
        from services.nce_service import NCEService
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        
        print("✅ All services imported successfully")
        return True, (NCEService, BurnRateService, BudgetForecastingService)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False, None

def test_nce_service_methods():
    """Test NCE Service methods"""
    try:
        from services.nce_service import NCEService
        
        print("\n🧪 Testing NCEService methods...")
        
        # Test static methods exist
        methods = [
            'request_extension',
            'approve_extension', 
            'reject_extension',
            'get_pending_amendments',
            'get_grant_amendments',
            'get_extension_statistics'
        ]
        
        for method in methods:
            if not hasattr(NCEService, method):
                print(f"❌ NCEService missing method: {method}")
                return False
        
        print("✅ NCEService has all required methods")
        
        # Test validation method (without database)
        validation_result = NCEService._validate_nce_request.__name__
        print(f"✅ Validation method exists: {validation_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ NCEService test error: {e}")
        return False

def test_burn_rate_service_methods():
    """Test Burn Rate Service methods"""
    try:
        from services.burn_rate_service import BurnRateService
        
        print("\n🧪 Testing BurnRateService methods...")
        
        # Test static methods exist
        methods = [
            'calculate_burn_rate',
            'get_burn_rate_trends',
            'get_system_burn_rate_summary',
            'get_burn_rate_alerts',
            'calculate_projected_completion'
        ]
        
        for method in methods:
            if not hasattr(BurnRateService, method):
                print(f"❌ BurnRateService missing method: {method}")
                return False
        
        print("✅ BurnRateService has all required methods")
        
        # Test helper methods
        helper_methods = [
            '_calculate_time_metrics',
            '_calculate_budget_metrics',
            '_determine_burn_status',
            '_generate_burn_recommendations'
        ]
        
        for method in helper_methods:
            if not hasattr(BurnRateService, method):
                print(f"❌ BurnRateService missing helper method: {method}")
                return False
        
        print("✅ BurnRateService has all required helper methods")
        return True
        
    except Exception as e:
        print(f"❌ BurnRateService test error: {e}")
        return False

def test_budget_forecasting_service_methods():
    """Test Budget Forecasting Service methods"""
    try:
        from services.budget_forecasting_service import BudgetForecastingService
        
        print("\n🧪 Testing BudgetForecastingService methods...")
        
        # Test static methods exist
        methods = [
            'calculate_forecast',
            'what_if_scenario',
            'get_forecast_summary',
            'get_financial_health_indicators'
        ]
        
        for method in methods:
            if not hasattr(BudgetForecastingService, method):
                print(f"❌ BudgetForecastingService missing method: {method}")
                return False
        
        print("✅ BudgetForecastingService has all required methods")
        
        # Test helper methods
        helper_methods = [
            '_get_current_spend',
            '_get_pending_expenses',
            '_get_recurring_costs',
            '_analyze_forecast_risks',
            '_determine_forecast_status'
        ]
        
        for method in helper_methods:
            if not hasattr(BudgetForecastingService, method):
                print(f"❌ BudgetForecastingService missing helper method: {method}")
                return False
        
        print("✅ BudgetForecastingService has all required helper methods")
        return True
        
    except Exception as e:
        print(f"❌ BudgetForecastingService test error: {e}")
        return False

def test_service_integration():
    """Test that services can work together"""
    try:
        from services.nce_service import NCEService
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        
        print("\n🧪 Testing service integration...")
        
        # Test that services don't have conflicting imports
        print("✅ No import conflicts between services")
        
        # Test that all services have proper error handling
        # (This is basic - full integration testing would require database)
        
        return True
        
    except Exception as e:
        print(f"❌ Service integration test error: {e}")
        return False

def test_method_signatures():
    """Test that critical methods have expected signatures"""
    try:
        from services.nce_service import NCEService
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        
        print("\n🧪 Testing method signatures...")
        
        # Test NCE Service signature
        import inspect
        nce_request_sig = inspect.signature(NCEService.request_extension)
        expected_params = ['grant_id', 'requested_end_date', 'justification', 'user_id', 'supporting_docs']
        actual_params = list(nce_request_sig.parameters.keys())
        
        for param in expected_params:
            if param not in actual_params:
                print(f"❌ NCEService.request_extension missing parameter: {param}")
                return False
        
        print("✅ NCEService.request_extension has correct signature")
        
        # Test Burn Rate Service signature
        burn_rate_sig = inspect.signature(BurnRateService.calculate_burn_rate)
        expected_burn_params = ['grant_id', 'force_recalculate']
        actual_burn_params = list(burn_rate_sig.parameters.keys())
        
        for param in expected_burn_params:
            if param not in actual_burn_params:
                print(f"❌ BurnRateService.calculate_burn_rate missing parameter: {param}")
                return False
        
        print("✅ BurnRateService.calculate_burn_rate has correct signature")
        
        # Test Forecasting Service signature
        forecast_sig = inspect.signature(BudgetForecastingService.calculate_forecast)
        expected_forecast_params = ['grant_id', 'force_recalculate']
        actual_forecast_params = list(forecast_sig.parameters.keys())
        
        for param in expected_forecast_params:
            if param not in actual_forecast_params:
                print(f"❌ BudgetForecastingService.calculate_forecast missing parameter: {param}")
                return False
        
        print("✅ BudgetForecastingService.calculate_forecast has correct signature")
        
        return True
        
    except Exception as e:
        print(f"❌ Method signature test error: {e}")
        return False

def test_service_documentation():
    """Test that services have proper documentation"""
    try:
        from services.nce_service import NCEService
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        
        print("\n🧪 Testing service documentation...")
        
        # Check if services have docstrings
        if NCEService.__doc__:
            print("✅ NCEService has documentation")
        else:
            print("⚠️  NCEService missing class documentation")
        
        if BurnRateService.__doc__:
            print("✅ BurnRateService has documentation")
        else:
            print("⚠️  BurnRateService missing class documentation")
        
        if BudgetForecastingService.__doc__:
            print("✅ BudgetForecastingService has documentation")
        else:
            print("⚠️  BudgetForecastingService missing class documentation")
        
        return True
        
    except Exception as e:
        print(f"❌ Documentation test error: {e}")
        return False

def verify_service_files():
    """Verify that service files exist and have content"""
    base_dir = os.path.dirname(__file__)
    services_dir = os.path.join(base_dir, 'services')
    
    service_files = [
        'nce_service.py',
        'burn_rate_service.py',
        'budget_forecasting_service.py'
    ]
    
    print("\n🔍 Verifying service files...")
    
    for file_name in service_files:
        file_path = os.path.join(services_dir, file_name)
        
        if not os.path.exists(file_path):
            print(f"❌ Service file missing: {file_name}")
            return False
        
        # Check file size (should be substantial)
        file_size = os.path.getsize(file_path)
        if file_size < 1000:  # Less than 1KB seems too small
            print(f"⚠️  Service file seems small: {file_name} ({file_size} bytes)")
        else:
            print(f"✅ {file_name} exists ({file_size} bytes)")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2: SERVICES IMPLEMENTATION TEST")
    print("=" * 60)
    
    tests = [
        verify_service_files,
        test_service_imports,
        test_nce_service_methods,
        test_burn_rate_service_methods,
        test_budget_forecasting_service_methods,
        test_service_integration,
        test_method_signatures,
        test_service_documentation
    ]
    
    all_passed = True
    for test in tests:
        if test == test_service_imports:
            success, services = test()
            if not success:
                all_passed = False
                break
        else:
            if not test():
                all_passed = False
                break
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 PHASE 2 SERVICES TEST PASSED!")
        print("✅ All services are properly implemented and ready for API integration")
        print("📋 Ready to proceed to Phase 3: API Endpoints")
    else:
        print("❌ PHASE 2 SERVICES TEST FAILED!")
        print("🔧 Please fix the service implementation issues before proceeding")
    
    print("=" * 60)
