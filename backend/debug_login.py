#!/usr/bin/env python3
"""
Debug the login 500 error
"""

import sys
import traceback

def debug_login():
    print("🔍 Debugging login 500 error...")
    
    try:
        # Test app creation
        print("1. Creating app...")
        from app import create_app
        app = create_app()
        print("   ✅ App created")
        
        # Test database setup
        print("2. Setting up database...")
        from app import setup_database
        setup_database(app)
        print("   ✅ Database setup")
        
        # Test with app context
        with app.app_context():
            print("3. Checking database...")
            from models import User, db
            
            # Check if users exist
            user_count = User.query.count()
            print(f"   Users in database: {user_count}")
            
            # Create test user if needed
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                print("   Creating test user...")
                test_user = User(
                    name='Test User',
                    email='test@example.com',
                    role='Team'
                )
                test_user.set_password('test')
                db.session.add(test_user)
                db.session.commit()
                print("   ✅ Test user created")
            else:
                print("   ✅ Test user exists")
            
            # Test login directly
            print("4. Testing login service...")
            from services.auth_service import AuthService
            user = AuthService.login('test@example.com', 'test')
            if user:
                print(f"   ✅ Login service works: {user.name}")
            else:
                print("   ❌ Login service failed")
                return
            
            # Test login endpoint
            print("5. Testing login endpoint...")
            with app.test_client() as client:
                response = client.post('/api/login', 
                                     json={'email': 'test@example.com', 'password': 'test'},
                                     content_type='application/json')
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.get_json()}")
                
                if response.status_code == 500:
                    print("   ❌ Login endpoint returned 500")
                    # Try to get more error info
                    try:
                        # Simulate the exact request
                        from flask import request
                        with app.test_request_context(json={'email': 'test@example.com', 'password': 'test'}):
                            from routes.auth import login
                            try:
                                result = login()
                                print(f"   Direct call result: {result}")
                            except Exception as e:
                                print(f"   Direct call error: {e}")
                                traceback.print_exc()
                    except Exception as e:
                        print(f"   Context error: {e}")
                else:
                    print("   ✅ Login endpoint working")
        
        print("\n🎉 Login debugging complete!")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == '__main__':
    debug_login()
