#!/usr/bin/env python3
"""
Test script to debug app startup issues
"""

import sys
import os

print("🔍 Testing App Startup")
print("=" * 40)

# Test 1: Check Python version
print(f"Python version: {sys.version}")

# Test 2: Check current directory
print(f"Current directory: {os.getcwd()}")

# Test 3: Try importing modules one by one
try:
    print("\n📦 Testing imports...")
    
    # Test basic imports
    print("  - Importing Flask...")
    from flask import Flask
    print("    ✅ Flask imported")
    
    print("  - Importing models...")
    from models import db
    print("    ✅ Models imported")
    
    print("  - Importing middleware...")
    from middleware.auth import token_required
    print("    ✅ Middleware imported")
    
    print("  - Importing routes...")
    from routes.assets import assets_bp
    print("    ✅ Assets routes imported")
    
    print("  - Importing asset analytics...")
    from routes.asset_analytics import analytics_bp
    print("    ✅ Analytics routes imported")
    
    print("  - Importing other asset routes...")
    from routes.asset_reporting import reporting_bp
    from routes.asset_documents import documents_bp
    from routes.asset_audit import audit_bp
    from routes.asset_forecasting import forecasting_bp
    from routes.asset_performance import performance_bp
    from routes.asset_barcodes import barcodes_bp
    from routes.asset_export_import import export_import_bp
    print("    ✅ All asset routes imported")
    
    # Test 4: Try creating app
    print("\n🏗️  Testing app creation...")
    from app import create_app
    app = create_app()
    print("    ✅ App created successfully")
    
    # Test 5: Test app configuration
    print("\n⚙️  Testing app configuration...")
    print(f"    - Secret key: {'✅ Set' if app.secret_key else '❌ Not set'}")
    print(f"    - Debug mode: {app.debug}")
    print(f"    - Registered blueprints: {len(app.blueprints)}")
    
    # Test 6: Test health endpoint
    print("\n🏥 Testing health endpoint...")
    with app.test_client() as client:
        response = client.get('/health')
        print(f"    - Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"    - Response: {response.get_json()}")
        else:
            print(f"    - Error: {response.get_data().decode()}")
    
    print("\n🎉 All tests passed! The app is ready to run.")
    print("\n🚀 To start the server, run:")
    print("   python app.py")
    print("   or")
    print("   flask run")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 40)
print("Test completed!")
