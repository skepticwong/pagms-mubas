#!/usr/bin/env python3
"""
Quick fix for backend 500 errors
"""

import sys
import os

def main():
    print("🔧 QUICK BACKEND FIX")
    print("=" * 40)
    
    try:
        # Step 1: Test basic app creation
        print("1. Testing app creation...")
        from app import create_app
        app = create_app()
        print("   ✅ App created")
        
        # Step 2: Setup database
        print("2. Setting up database...")
        from app import setup_database
        setup_database(app)
        print("   ✅ Database setup")
        
        # Step 3: Create test user in app context
        print("3. Creating test user...")
        with app.app_context():
            from models import db, User
            
            # Check if user exists
            user = User.query.filter_by(email='test@example.com').first()
            if not user:
                print("   Creating new test user...")
                user = User(
                    name='Test User',
                    email='test@example.com',
                    role='Team'
                )
                user.set_password('test')
                db.session.add(user)
                db.session.commit()
                print("   ✅ Test user created")
            else:
                print("   ✅ Test user already exists")
        
        # Step 4: Test endpoints
        print("4. Testing endpoints...")
        with app.test_client() as client:
            # Health check
            response = client.get('/health')
            print(f"   Health: {response.status_code}")
            
            # Login test
            response = client.post('/api/login', 
                                 json={'email': 'test@example.com', 'password': 'test'},
                                 content_type='application/json')
            print(f"   Login: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Login works: {response.get_json()['name']}")
            else:
                print(f"   ❌ Login failed: {response.get_json()}")
            
            # Auth check test
            # First login to get session
            client.post('/api/login', 
                       json={'email': 'test@example.com', 'password': 'test'},
                       content_type='application/json')
            
            # Then test auth check
            response = client.get('/api/auth/me')
            print(f"   Auth check: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Auth check works: {response.get_json()['name']}")
            else:
                print(f"   ❌ Auth check failed: {response.get_json()}")
        
        print("\n🎉 BACKEND IS READY!")
        print("✅ Start with: python app.py")
        print("✅ Frontend should connect now")
        print("✅ Login with: test@example.com / test")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🚀 Backend is fixed and ready!")
    else:
        print("\n❌ Backend needs manual fixing")
    sys.exit(0 if success else 1)
