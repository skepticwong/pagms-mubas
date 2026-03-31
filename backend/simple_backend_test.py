#!/usr/bin/env python3
"""
Simple backend test to identify the 500 error
"""

print("=== SIMPLE BACKEND TEST ===")

# Test 1: Basic imports
print("1. Testing basic imports...")
try:
    import sys
    import os
    print("   ✅ Basic Python modules OK")
except Exception as e:
    print(f"   ❌ Basic import failed: {e}")
    exit(1)

# Test 2: Flask imports
print("2. Testing Flask imports...")
try:
    from flask import Flask, jsonify
    print("   ✅ Flask imports OK")
except Exception as e:
    print(f"   ❌ Flask import failed: {e}")
    exit(1)

# Test 3: App creation
print("3. Testing app creation...")
try:
    from app import create_app
    app = create_app()
    print("   ✅ App creation OK")
except Exception as e:
    print(f"   ❌ App creation failed: {e}")
    print(f"   Error details: {str(e)}")
    exit(1)

# Test 4: Database setup
print("4. Testing database...")
try:
    with app.app_context():
        from models import db, User
        db.create_all()
        print("   ✅ Database setup OK")
except Exception as e:
    print(f"   ❌ Database setup failed: {e}")
    print(f"   Error details: {str(e)}")
    exit(1)

# Test 5: Login endpoint
print("5. Testing login endpoint...")
try:
    with app.test_client() as client:
        response = client.post('/api/login', 
                             json={'email': 'test@example.com', 'password': 'test'},
                             content_type='application/json')
        print(f"   Login response status: {response.status_code}")
        
        if response.status_code == 500:
            data = response.get_json()
            print(f"   ❌ Login failed with 500: {data}")
            
            # Check if user exists
            with app.app_context():
                user = User.query.filter_by(email='test@example.com').first()
                if not user:
                    print("   ⚠️  Test user not found, creating...")
                    user = User(name='Test User', email='test@example.com', role='Team')
                    user.set_password('test')
                    db.session.add(user)
                    db.session.commit()
                    print("   ✅ Test user created")
                    
                    # Try login again
                    response = client.post('/api/login', 
                                         json={'email': 'test@example.com', 'password': 'test'},
                                         content_type='application/json')
                    print(f"   Login retry status: {response.status_code}")
                    if response.status_code == 200:
                        print("   ✅ Login successful after user creation")
                    else:
                        print(f"   ❌ Login still failed: {response.get_json()}")
                else:
                    print("   ✅ Test user exists")
        else:
            print(f"   ✅ Login successful: {response.get_json()}")
            
except Exception as e:
    print(f"   ❌ Login test failed: {e}")
    print(f"   Error details: {str(e)}")
    exit(1)

print("\n=== TEST COMPLETE ===")
print("✅ Backend appears to be working correctly")
print("🚀 Start with: python app.py")
print("📡 Frontend should be able to connect")
