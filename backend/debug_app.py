#!/usr/bin/env python3
"""
Debug script to test app startup step by step
"""

import sys
import os

def test_imports():
    """Test all imports step by step"""
    print("🔍 Testing imports...")
    
    try:
        print("  - Importing basic Flask modules...")
        from flask import Flask, jsonify
        print("    ✅ Flask imported")
        
        print("  - Importing models...")
        from models import db, Asset, AssetMaintenance, AssetTransfer, Grant, User
        print("    ✅ Models imported")
        
        print("  - Importing middleware...")
        from middleware.auth import token_required
        print("    ✅ Middleware imported")
        
        print("  - Importing services...")
        from services.asset_service import AssetService
        from services.asset_analytics_service import AssetAnalyticsService
        from services.asset_reporting_service import AssetReportingService
        from services.asset_document_service import AssetDocumentService
        from services.asset_audit_service import AssetAuditService
        from services.asset_barcode_service import AssetBarcodeService
        from services.asset_export_service import AssetExportService
        print("    ✅ All services imported")
        
        print("  - Importing routes...")
        from routes.assets import assets_bp
        from routes.asset_analytics import analytics_bp
        from routes.asset_reporting import reporting_bp
        from routes.asset_documents import documents_bp
        from routes.asset_audit import audit_bp
        from routes.asset_forecasting import forecasting_bp
        from routes.asset_performance import performance_bp
        from routes.asset_barcodes import barcodes_bp
        from routes.asset_export_import import export_import_bp
        print("    ✅ All routes imported")
        
        print("  - Importing app...")
        from app import create_app
        print("    ✅ App imported")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test app creation"""
    print("🏗️  Testing app creation...")
    
    try:
        from app import create_app
        app = create_app()
        print("  ✅ App created successfully")
        
        # Test app configuration
        print(f"  - Secret key: {'✅ Set' if app.secret_key else '❌ Not set'}")
        print(f"  - Debug mode: {app.debug}")
        print(f"  - Registered blueprints: {len(app.blueprints)}")
        
        # Test health endpoint
        print("  - Testing health endpoint...")
        with app.test_client() as client:
            response = client.get('/health')
            print(f"    Status code: {response.status_code}")
            if response.status_code == 200:
                print(f"    Response: {response.get_json()}")
            else:
                print(f"    Error: {response.get_data().decode()}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ App creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Debugging PAGMS Asset Management Backend")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    print("\n✅ All imports passed!")
    
    # Test app creation
    if not test_app_creation():
        print("\n❌ App creation tests failed!")
        return False
    
    print("\n✅ All tests passed!")
    print("\n🎉 The app is ready to run!")
    print("🚀 To start the server, run:")
    print("   python app.py")
    print("   or")
    print("   python start_app.py")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
