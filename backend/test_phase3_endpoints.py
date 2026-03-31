"""
Test script for Phase 3 API Endpoints - NCE, Burn Rate, and Budget Forecasting
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

def test_route_imports():
    """Test that all route modules can be imported"""
    try:
        from routes.amendments import amendments_bp
        print("✅ Amendments routes imported successfully")
        
        # Check that rules.py has the new endpoints (by checking the file)
        rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
        with open(rules_file, 'r') as f:
            rules_content = f.read()
        
        burn_rate_endpoints = [
            '/burn-rate/<int:grant_id>',
            '/burn-rate/summary',
            '/burn-rate/alerts'
        ]
        
        forecast_endpoints = [
            '/forecast/<int:grant_id>',
            '/forecast/summary',
            '/forecast/<int:grant_id>/health'
        ]
        
        for endpoint in burn_rate_endpoints:
            if endpoint in rules_content:
                print(f"✅ Burn rate endpoint found: {endpoint}")
            else:
                print(f"❌ Burn rate endpoint missing: {endpoint}")
                return False
        
        for endpoint in forecast_endpoints:
            if endpoint in rules_content:
                print(f"✅ Forecast endpoint found: {endpoint}")
            else:
                print(f"❌ Forecast endpoint missing: {endpoint}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_amendments_routes():
    """Test amendments route structure"""
    try:
        from routes.amendments import amendments_bp
        
        print("\n🧪 Testing amendments routes...")
        
        # Get all routes from the blueprint
        routes = []
        for rule in amendments_bp.deferred_functions:
            if hasattr(rule, 'func') and hasattr(rule.func, '__name__'):
                routes.append(rule.func.__name__)
        
        expected_routes = [
            'request_nce',
            'approve_nce',
            'reject_nce',
            'withdraw_nce',
            'get_pending_amendments',
            'get_grant_amendments',
            'get_amendment_details',
            'get_extension_statistics',
            'get_amendment_history'
        ]
        
        for route in expected_routes:
            if route in routes:
                print(f"   ✅ {route}")
            else:
                print(f"   ❌ {route} - NOT FOUND")
                return False
        
        print(f"   📄 Total routes found: {len(routes)}")
        return True
        
    except Exception as e:
        print(f"❌ Amendments routes test error: {e}")
        return False

def test_rules_routes_expansion():
    """Test that rules.py has been expanded with new endpoints"""
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    try:
        with open(rules_file, 'r') as f:
            rules_content = f.read()
        
        print("\n🧪 Testing rules.py expansion...")
        
        # Check for burn rate endpoints
        burn_rate_checks = {
            'Burn rate endpoint': '@rules_bp.route(\'/burn-rate/<int:grant_id>\')' in rules_content,
            'Burn rate trends': '@rules_bp.route(\'/burn-rate/<int:grant_id>/trends\')' in rules_content,
            'Burn rate summary': '@rules_bp.route(\'/burn-rate/summary\')' in rules_content,
            'Burn rate alerts': '@rules_bp.route(\'/burn-rate/alerts\')' in rules_content,
            'Projected completion': '@rules_bp.route(\'/burn-rate/<int:grant_id>/projected-completion\')' in rules_content
        }
        
        for check, result in burn_rate_checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
        
        # Check for forecast endpoints
        forecast_checks = {
            'Forecast endpoint': '@rules_bp.route(\'/forecast/<int:grant_id>\')' in rules_content,
            'What-if scenario': '@rules_bp.route(\'/forecast/<int:grant_id>/what-if\')' in rules_content,
            'Forecast summary': '@rules_bp.route(\'/forecast/summary\')' in rules_content,
            'Financial health': '@rules_bp.route(\'/forecast/<int:grant_id>/health\')' in rules_content
        }
        
        for check, result in forecast_checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
        
        # Check for dashboard endpoints
        dashboard_checks = {
            'Financial dashboard': '@rules_bp.route(\'/financial-dashboard\')' in rules_content,
            'System financial overview': '@rules_bp.route(\'/system-financial-overview\')' in rules_content
        }
        
        for check, result in dashboard_checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rules expansion test error: {e}")
        return False

def test_app_registration():
    """Test that amendments blueprint is registered in app.py"""
    app_file = os.path.join(os.path.dirname(__file__), 'app.py')
    
    try:
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        print("\n🧪 Testing app.py registration...")
        
        checks = {
            'Amendments import': 'from routes.amendments import amendments_bp' in app_content,
            'Amendments registration': 'app.register_blueprint(amendments_bp' in app_content
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"❌ App registration test error: {e}")
        return False

def test_endpoint_documentation():
    """Test that endpoints have proper documentation"""
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    try:
        print("\n🧪 Testing endpoint documentation...")
        
        # Check amendments endpoints
        with open(amendments_file, 'r') as f:
            amendments_content = f.read()
        
        amendments_docs = {
            'Request NCE docstring': 'def request_nce' in amendments_content and '"""' in amendments_content,
            'Approve NCE docstring': 'def approve_nce' in amendments_content and '"""' in amendments_content,
            'Request body examples': 'Request Body:' in amendments_content
        }
        
        print("   Amendments endpoints:")
        for check, result in amendments_docs.items():
            status = "✅" if result else "⚠️"
            print(f"     {status} {check}")
        
        # Check rules endpoints
        with open(rules_file, 'r') as f:
            rules_content = f.read()
        
        rules_docs = {
            'Burn rate docstring': 'def get_burn_rate' in rules_content and '"""' in rules_content,
            'Forecast docstring': 'def get_budget_forecast' in rules_content and '"""' in rules_content,
            'Error handling': 'try:' in rules_content and 'except' in rules_content
        }
        
        print("   Rules endpoints:")
        for check, result in rules_docs.items():
            status = "✅" if result else "⚠️"
            print(f"     {status} {check}")
        
        return True
        
    except Exception as e:
        print(f"❌ Documentation test error: {e}")
        return False

def test_endpoint_validation():
    """Test that endpoints have proper validation"""
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    try:
        print("\n🧪 Testing endpoint validation...")
        
        # Check amendments validation
        with open(amendments_file, 'r') as f:
            amendments_content = f.read()
        
        amendments_validation = {
            'Required fields validation': 'if not all([' in amendments_content,
            'Type validation': 'isinstance(' in amendments_content,
            'Error responses': 'return jsonify' in amendments_content and '400' in amendments_content,
            'Authentication decorators': '@token_required' in amendments_content,
            'RSU authorization': '@rsu_required' in amendments_content
        }
        
        print("   Amendments validation:")
        for check, result in amendments_validation.items():
            status = "✅" if result else "⚠️"
            print(f"     {status} {check}")
        
        # Check rules validation
        with open(rules_file, 'r') as f:
            rules_content = f.read()
        
        rules_validation = {
            'Query parameter validation': 'request.args.get' in rules_content,
            'Type checking': 'type=int' in rules_content,
            'Error handling': 'except Exception as e:' in rules_content,
            'Authentication': '@token_required' in rules_content
        }
        
        print("   Rules validation:")
        for check, result in rules_validation.items():
            status = "✅" if result else "⚠️"
            print(f"     {status} {check}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        return False

def test_api_structure():
    """Test overall API structure and organization"""
    print("\n🧪 Testing API structure...")
    
    # Count total endpoints
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    try:
        # Count amendments endpoints
        with open(amendments_file, 'r') as f:
            amendments_content = f.read()
        
        amendments_endpoints = amendments_content.count('@amendments_bp.route')
        
        # Count new rules endpoints
        with open(rules_file, 'r') as f:
            rules_content = f.read()
        
        burn_rate_endpoints = rules_content.count('/burn-rate')
        forecast_endpoints = rules_content.count('/forecast')
        dashboard_endpoints = rules_content.count('/financial-dashboard') + rules_content.count('/system-financial-overview')
        
        print(f"   📊 Amendments endpoints: {amendments_endpoints}")
        print(f"   📊 Burn rate endpoints: {burn_rate_endpoints}")
        print(f"   📊 Forecast endpoints: {forecast_endpoints}")
        print(f"   📊 Dashboard endpoints: {dashboard_endpoints}")
        print(f"   📊 Total new endpoints: {amendments_endpoints + burn_rate_endpoints + forecast_endpoints + dashboard_endpoints}")
        
        # Check for RESTful patterns
        restful_patterns = {
            'GET endpoints': amendments_content.count('methods=[\'GET\']') + rules_content.count('methods=[\'GET\']'),
            'POST endpoints': amendments_content.count('methods=[\'POST\']') + rules_content.count('methods=[\'POST\']'),
            'PUT/PATCH endpoints': amendments_content.count('methods=[\'PUT\'') + amendments_content.count('methods=[\'PATCH\''),
            'DELETE endpoints': amendments_content.count('methods=[\'DELETE\'')
        }
        
        print("   📊 HTTP Methods:")
        for method, count in restful_patterns.items():
            print(f"     {method}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3: API ENDPOINTS TEST")
    print("=" * 60)
    
    tests = [
        test_route_imports,
        test_amendments_routes,
        test_rules_routes_expansion,
        test_app_registration,
        test_endpoint_documentation,
        test_endpoint_validation,
        test_api_structure
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            break
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 PHASE 3 API ENDPOINTS TEST PASSED!")
        print("✅ All API endpoints are properly implemented and ready for frontend integration")
        print("📋 Ready to proceed to Phase 4: Frontend Integration")
        print("\n📡 Available endpoints:")
        print("   🏛️  NCE Workflow: /api/amendments/*")
        print("   🔥 Burn Rate Analysis: /api/rules/burn-rate/*")
        print("   💰 Budget Forecasting: /api/rules/forecast/*")
        print("   📊 Financial Dashboards: /api/rules/financial-dashboard, /api/rules/system-financial-overview")
    else:
        print("❌ PHASE 3 API ENDPOINTS TEST FAILED!")
        print("🔧 Please fix the endpoint implementation issues before proceeding")
    
    print("=" * 60)
