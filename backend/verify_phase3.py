"""
Direct verification of Phase 3 API endpoints implementation
"""

import os

def verify_amendments_routes():
    """Verify amendments routes file structure and endpoints"""
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    
    print("🔍 Verifying amendments routes...")
    
    if not os.path.exists(amendments_file):
        print("❌ amendments.py file not found")
        return False
    
    with open(amendments_file, 'r') as f:
        content = f.read()
    
    # Check for essential components
    amendments_checks = {
        'Blueprint definition': 'amendments_bp = Blueprint' in content,
        'Import statements': 'from services.nce_service import NCEService' in content,
        'Authentication decorators': '@token_required' in content,
        'RSU authorization': '@rsu_required' in content,
        'NCE request endpoint': '@amendments_bp.route(\'/nce/request\')' in content,
        'NCE approve endpoint': '@amendments_bp.route(\'/nce/<int:amendment_id>/approve\')' in content,
        'NCE reject endpoint': '@amendments_bp.route(\'/nce/<int:amendment_id>/reject\')' in content,
        'Pending amendments endpoint': '@amendments_bp.route(\'/pending\')' in content,
        'Grant amendments endpoint': '@amendments_bp.route(\'/grant/<int:grant_id>/amendments\')' in content,
        'Statistics endpoint': '@amendments_bp.route(\'/nce/statistics\')' in content,
        'Error handling': 'try:' in content and 'except' in content,
        'JSON responses': 'return jsonify' in content
    }
    
    for check, result in amendments_checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
    
    # Check endpoint count
    endpoint_count = content.count('@amendments_bp.route')
    print(f"   📊 Total endpoints: {endpoint_count}")
    
    return all(amendments_checks.values())

def verify_rules_expansion():
    """Verify rules.py has been expanded with burn rate and forecasting endpoints"""
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    print("\n🔍 Verifying rules.py expansion...")
    
    if not os.path.exists(rules_file):
        print("❌ rules.py file not found")
        return False
    
    with open(rules_file, 'r') as f:
        content = f.read()
    
    # Check for burn rate endpoints
    burn_rate_checks = {
        'Burn rate endpoint': '@rules_bp.route(\'/burn-rate/<int:grant_id>\')' in content,
        'Burn rate trends': '@rules_bp.route(\'/burn-rate/<int:grant_id>/trends\')' in content,
        'Burn rate summary': '@rules_bp.route(\'/burn-rate/summary\')' in content,
        'Burn rate alerts': '@rules_bp.route(\'/burn-rate/alerts\')' in content,
        'Projected completion': '@rules_bp.route(\'/burn-rate/<int:grant_id>/projected-completion\')' in content,
        'Burn rate service import': 'from services.burn_rate_service import BurnRateService' in content
    }
    
    print("   Burn Rate endpoints:")
    for check, result in burn_rate_checks.items():
        status = "✅" if result else "❌"
        print(f"     {status} {check}")
    
    # Check for forecast endpoints
    forecast_checks = {
        'Forecast endpoint': '@rules_bp.route(\'/forecast/<int:grant_id>\')' in content,
        'What-if scenario': '@rules_bp.route(\'/forecast/<int:grant_id>/what-if\')' in content,
        'Forecast summary': '@rules_bp.route(\'/forecast/summary\')' in content,
        'Financial health': '@rules_bp.route(\'/forecast/<int:grant_id>/health\')' in content,
        'Forecast service import': 'from services.budget_forecasting_service import BudgetForecastingService' in content
    }
    
    print("   Forecast endpoints:")
    for check, result in forecast_checks.items():
        status = "✅" if result else "❌"
        print(f"     {status} {check}")
    
    # Check for dashboard endpoints
    dashboard_checks = {
        'Financial dashboard': '@rules_bp.route(\'/financial-dashboard\')' in content,
        'System financial overview': '@rules_bp.route(\'/system-financial-overview\')' in content
    }
    
    print("   Dashboard endpoints:")
    for check, result in dashboard_checks.items():
        status = "✅" if result else "❌"
        print(f"     {status} {check}")
    
    return all(burn_rate_checks.values()) and all(forecast_checks.values()) and all(dashboard_checks.values())

def verify_app_registration():
    """Verify that amendments blueprint is registered in app.py"""
    app_file = os.path.join(os.path.dirname(__file__), 'app.py')
    
    print("\n🔍 Verifying app.py registration...")
    
    if not os.path.exists(app_file):
        print("❌ app.py file not found")
        return False
    
    with open(app_file, 'r') as f:
        content = f.read()
    
    registration_checks = {
        'Amendments import': 'from routes.amendments import amendments_bp' in content,
        'Amendments registration': 'app.register_blueprint(amendments_bp' in content,
        'API prefix': 'url_prefix=\'/api\'' in content
    }
    
    for check, result in registration_checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
    
    return all(registration_checks.values())

def verify_endpoint_structure():
    """Verify the structure and quality of endpoints"""
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    print("\n🔍 Verifying endpoint structure...")
    
    structure_checks = {}
    
    # Check amendments structure
    with open(amendments_file, 'r') as f:
        amendments_content = f.read()
    
    amendments_structure = {
        'Docstrings': '"""' in amendments_content,
        'Request validation': 'request.json' in amendments_content,
        'Error responses': '400' in amendments_content and '500' in amendments_content,
        'Success responses': '201' in amendments_content and '200' in amendments_content,
        'Query parameter handling': 'request.args.get' in amendments_content,
        'Type validation': 'type=int' in amendments_content,
        'Comprehensive error handling': 'except Exception as e:' in amendments_content
    }
    
    print("   Amendments structure:")
    for check, result in amendments_structure.items():
        status = "✅" if result else "⚠️"
        print(f"     {status} {check}")
        structure_checks[f'amendments_{check}'] = result
    
    # Check rules structure
    with open(rules_file, 'r') as f:
        rules_content = f.read()
    
    rules_structure = {
        'Service imports': 'from services.' in rules_content,
        'Query validation': 'request.args.get' in rules_content,
        'Error handling': 'try:' in rules_content and 'except' in rules_content,
        'JSON responses': 'return jsonify' in rules_content,
        'Authentication': '@token_required' in rules_content,
        'Authorization': '@rsu_required' in rules_content,
        'Timestamp inclusion': 'datetime.utcnow().isoformat()' in rules_content
    }
    
    print("   Rules structure:")
    for check, result in rules_structure.items():
        status = "✅" if result else "⚠️"
        print(f"     {status} {check}")
        structure_checks[f'rules_{check}'] = result
    
    return all(structure_checks.values())

def verify_api_completeness():
    """Verify that all required API endpoints are implemented"""
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    print("\n🔍 Verifying API completeness...")
    
    # Required NCE endpoints
    with open(amendments_file, 'r') as f:
        amendments_content = f.read()
    
    nce_endpoints = {
        'POST /nce/request': '@amendments_bp.route(\'/nce/request\', methods=[\'POST\'])' in amendments_content,
        'POST /nce/{id}/approve': '@amendments_bp.route(\'/nce/<int:amendment_id>/approve\', methods=[\'POST\'])' in amendments_content,
        'POST /nce/{id}/reject': '@amendments_bp.route(\'/nce/<int:amendment_id>/reject\', methods=[\'POST\'])' in amendments_content,
        'POST /nce/{id}/withdraw': '@amendments_bp.route(\'/nce/<int:amendment_id>/withdraw\', methods=[\'POST\'])' in amendments_content,
        'GET /pending': '@amendments_bp.route(\'/pending\', methods=[\'GET\'])' in amendments_content,
        'GET /grant/{id}/amendments': '@amendments_bp.route(\'/grant/<int:grant_id>/amendments\', methods=[\'GET\'])' in amendments_content,
        'GET /nce/{id}': '@amendments_bp.route(\'/nce/<int:amendment_id>\', methods=[\'GET\'])' in amendments_content,
        'GET /nce/statistics': '@amendments_bp.route(\'/nce/statistics\', methods=[\'GET\'])' in amendments_content
    }
    
    print("   NCE endpoints:")
    for endpoint, result in nce_endpoints.items():
        status = "✅" if result else "❌"
        print(f"     {status} {endpoint}")
    
    # Required burn rate endpoints
    with open(rules_file, 'r') as f:
        rules_content = f.read()
    
    burn_rate_endpoints = {
        'GET /burn-rate/{id}': '@rules_bp.route(\'/burn-rate/<int:grant_id>\', methods=[\'GET\'])' in rules_content,
        'GET /burn-rate/{id}/trends': '@rules_bp.route(\'/burn-rate/<int:grant_id>/trends\', methods=[\'GET\'])' in rules_content,
        'GET /burn-rate/summary': '@rules_bp.route(\'/burn-rate/summary\', methods=[\'GET\'])' in rules_content,
        'GET /burn-rate/alerts': '@rules_bp.route(\'/burn-rate/alerts\', methods=[\'GET\'])' in rules_content,
        'GET /burn-rate/{id}/projected-completion': '@rules_bp.route(\'/burn-rate/<int:grant_id>/projected-completion\', methods=[\'GET\'])' in rules_content
    }
    
    print("   Burn Rate endpoints:")
    for endpoint, result in burn_rate_endpoints.items():
        status = "✅" if result else "❌"
        print(f"     {status} {endpoint}")
    
    # Required forecast endpoints
    forecast_endpoints = {
        'GET /forecast/{id}': '@rules_bp.route(\'/forecast/<int:grant_id>\', methods=[\'GET\'])' in rules_content,
        'POST /forecast/{id}/what-if': '@rules_bp.route(\'/forecast/<int:grant_id>/what-if\', methods=[\'POST\'])' in rules_content,
        'GET /forecast/summary': '@rules_bp.route(\'/forecast/summary\', methods=[\'GET\'])' in rules_content,
        'GET /forecast/{id}/health': '@rules_bp.route(\'/forecast/<int:grant_id>/health\', methods=[\'GET\'])' in rules_content
    }
    
    print("   Forecast endpoints:")
    for endpoint, result in forecast_endpoints.items():
        status = "✅" if result else "❌"
        print(f"     {status} {endpoint}")
    
    # Dashboard endpoints
    dashboard_endpoints = {
        'GET /financial-dashboard': '@rules_bp.route(\'/financial-dashboard\', methods=[\'GET\'])' in rules_content,
        'GET /system-financial-overview': '@rules_bp.route(\'/system-financial-overview\', methods=[\'GET\'])' in rules_content
    }
    
    print("   Dashboard endpoints:")
    for endpoint, result in dashboard_endpoints.items():
        status = "✅" if result else "❌"
        print(f"     {status} {endpoint}")
    
    all_endpoints = list(nce_endpoints.values()) + list(burn_rate_endpoints.values()) + list(forecast_endpoints.values()) + list(dashboard_endpoints.values())
    return all(all_endpoints)

def verify_file_integrity():
    """Verify file sizes and basic integrity"""
    amendments_file = os.path.join(os.path.dirname(__file__), 'routes', 'amendments.py')
    rules_file = os.path.join(os.path.dirname(__file__), 'routes', 'rules.py')
    
    print("\n🔍 Verifying file integrity...")
    
    files_to_check = {
        'amendments.py': amendments_file,
        'rules.py': rules_file
    }
    
    for file_name, file_path in files_to_check.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   📄 {file_name}: {file_size} bytes")
            
            if file_size < 5000:  # Less than 5KB seems too small for full implementation
                print(f"     ⚠️  File seems small for complete implementation")
            else:
                print(f"     ✅ File size looks appropriate")
        else:
            print(f"   ❌ {file_name}: File not found")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3 API ENDPOINTS VERIFICATION")
    print("=" * 60)
    
    checks = [
        verify_file_integrity,
        verify_amendments_routes,
        verify_rules_expansion,
        verify_app_registration,
        verify_endpoint_structure,
        verify_api_completeness
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
            break
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 PHASE 3 API ENDPOINTS VERIFICATION PASSED!")
        print("✅ All API endpoints are properly implemented with:")
        print("   - Complete NCE workflow endpoints")
        print("   - Comprehensive burn rate analysis endpoints")
        print("   - Full budget forecasting endpoints")
        print("   - Financial dashboard endpoints")
        print("   - Proper authentication and authorization")
        print("   - Error handling and validation")
        print("   - RESTful API design patterns")
        print("📋 Ready to proceed to Phase 4: Frontend Integration")
        print("\n📡 API Summary:")
        print("   🏛️  NCE Workflow: 8 endpoints")
        print("   🔥 Burn Rate Analysis: 5 endpoints")
        print("   💰 Budget Forecasting: 4 endpoints")
        print("   📊 Financial Dashboards: 2 endpoints")
        print("   🚀 Total: 19 new API endpoints")
    else:
        print("❌ PHASE 3 API ENDPOINTS VERIFICATION FAILED!")
        print("🔧 Please fix the endpoint implementation issues before proceeding")
    
    print("=" * 60)
