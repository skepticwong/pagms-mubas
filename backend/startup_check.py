#!/usr/bin/env python3
"""
Comprehensive startup check for the backend
"""

import sys
import os

def check_imports():
    """Check all critical imports"""
    print("🔍 Checking imports...")
    
    try:
        from app import create_app
        print("✅ App import successful")
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    try:
        from models import db, User, Grant, GrantAmendment, GrantFinancialMetrics
        print("✅ Models import successful")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from services.nce_service import NCEService
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        print("✅ Services import successful")
    except Exception as e:
        print(f"❌ Services import failed: {e}")
        return False
    
    try:
        from routes.amendments import amendments_bp
        print("✅ Amendments route import successful")
    except Exception as e:
        print(f"❌ Amendments route import failed: {e}")
        return False
    
    return True

def check_database():
    """Check database setup"""
    print("\n🔍 Checking database...")
    
    try:
        from app import create_app, setup_database
        app = create_app()
        
        with app.app_context():
            setup_database(app)
            print("✅ Database setup successful")
            
            from models import User
            user_count = User.query.count()
            print(f"✅ Database accessible - {user_count} users found")
            
            if user_count == 0:
                print("⚠️  No users in database - creating test user...")
                test_user = User(
                    name='Test User',
                    email='test@example.com',
                    role='Team'
                )
                test_user.set_password('test')
                from models import db
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created")
            
            return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_endpoints():
    """Check critical endpoints"""
    print("\n🔍 Checking endpoints...")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.test_client() as client:
            # Health check
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Login check
            response = client.post('/api/login', 
                                 json={'email': 'test@example.com', 'password': 'test'},
                                 content_type='application/json')
            if response.status_code == 200:
                print("✅ Login endpoint working")
                print(f"   User data: {response.get_json()}")
            else:
                print(f"❌ Login endpoint failed: {response.status_code}")
                print(f"   Error: {response.get_json()}")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Endpoint check failed: {e}")
        return False

def main():
    print("=" * 60)
    print("BACKEND STARTUP CHECK")
    print("=" * 60)
    
    checks = [
        ("Imports", check_imports),
        ("Database", check_database),
        ("Endpoints", check_endpoints)
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
            break
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Backend is ready to start")
        print("\n🚀 Start with: python app.py")
        print("📡 Frontend can connect to: http://localhost:5000")
    else:
        print("❌ STARTUP CHECK FAILED!")
        print("🔧 Please fix the issues above before starting the backend")
    print("=" * 60)

if __name__ == '__main__':
    main()
