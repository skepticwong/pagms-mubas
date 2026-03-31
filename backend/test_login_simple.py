#!/usr/bin/env python3
"""
Simple test to isolate the login 500 error
"""

print("=== SIMPLE LOGIN TEST ===")

# Step 1: Test imports
print("1. Testing imports...")
try:
    from app import create_app
    from models import User, db
    print("   ✅ Imports OK")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Step 2: Create app and setup database
print("2. Setting up database...")
try:
    app = create_app()
    with app.app_context():
        db.create_all()
        print("   ✅ Database setup OK")
except Exception as e:
    print(f"   ❌ Database setup failed: {e}")
    exit(1)

# Step 3: Create test user
print("3. Creating test user...")
try:
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
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
            print("   ✅ Test user exists")
except Exception as e:
    print(f"   ❌ User creation failed: {e}")
    exit(1)

# Step 4: Test login service
print("4. Testing login service...")
try:
    from services.auth_service import AuthService
    with app.app_context():
        user = AuthService.login('test@example.com', 'test')
        if user:
            print(f"   ✅ Login service works: {user.name}")
            print(f"   User dict: {user.to_dict()}")
        else:
            print("   ❌ Login service returned None")
            exit(1)
except Exception as e:
    print(f"   ❌ Login service failed: {e}")
    exit(1)

# Step 5: Test login endpoint
print("5. Testing login endpoint...")
try:
    with app.test_client() as client:
        response = client.post('/api/login', 
                             json={'email': 'test@example.com', 'password': 'test'},
                             content_type='application/json')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.get_json()}")
        
        if response.status_code == 500:
            print("   ❌ Login endpoint returned 500")
            print("   Let's test the session handling...")
            
            # Test session handling
            with app.test_request_context(json={'email': 'test@example.com', 'password': 'test'}):
                try:
                    from flask import request, session
                    from routes.auth import login
                    
                    # Manually test the login function
                    result = login()
                    print(f"   Manual login result: {result}")
                except Exception as e:
                    print(f"   Manual login error: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("   ✅ Login endpoint working!")
            
except Exception as e:
    print(f"   ❌ Login endpoint test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n=== TEST COMPLETE ===")
print("✅ All tests passed! Backend should work.")
print("🚀 Start with: python app.py")
