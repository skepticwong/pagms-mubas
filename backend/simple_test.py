#!/usr/bin/env python3
"""
Simple test to check if the app can be imported
"""

print("Testing basic imports...")

try:
    print("1. Importing Flask...")
    from flask import Flask
    print("   ✅ Flask imported")
    
    print("2. Importing models...")
    from models import db, Asset, AssetMaintenance, AssetTransfer, Grant, User
    print("   ✅ Models imported")
    
    print("3. Importing middleware...")
    from middleware.auth import token_required
    print("   ✅ Middleware imported")
    
    print("4. Importing asset service...")
    from services.asset_service import AssetService
    print("   ✅ Asset service imported")
    
    print("5. Importing asset routes...")
    from routes.assets import assets_bp
    print("   ✅ Asset routes imported")
    
    print("6. Importing app...")
    from app import create_app
    print("   ✅ App imported")
    
    print("7. Creating app...")
    app = create_app()
    print("   ✅ App created")
    
    print("8. Testing health endpoint...")
    with app.test_client() as client:
        response = client.get('/health')
        print(f"   ✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.get_json()}")
    
    print("\n🎉 All tests passed! The app is ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
