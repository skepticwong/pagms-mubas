#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing grants endpoint directly...")

try:
    # Test imports
    from flask import Flask, session, jsonify
    print("✓ Flask imported")
    
    # Import models
    from models import db, User, Grant, BudgetCategory
    print("✓ Models imported")
    
    # Import grant service
    from services.grant_service import GrantService
    print("✓ GrantService imported")
    
    # Create minimal app context
    app = Flask(__name__)
    app.secret_key = 'test-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if users exist
        user_count = User.query.count()
        print(f"Users in database: {user_count}")
        
        if user_count == 0:
            print("Creating test user...")
            test_user = User(
                name="Test PI",
                email="test@example.com",
                role="PI",
                password="test123"
            )
            db.session.add(test_user)
            db.session.commit()
            print("✓ Test user created")
        
        # Test GrantService.get_grants_for_user
        users = User.query.all()
        if users:
            test_user = users[0]
            print(f"Testing get_grants_for_user for user: {test_user.name} (ID: {test_user.id})")
            
            try:
                grants = GrantService.get_grants_for_user(test_user.id)
                print(f"✓ get_grants_for_user returned {len(grants)} grants")
                for grant in grants:
                    print(f"  - {grant.get('title', 'No title')}")
            except Exception as e:
                print(f"✗ get_grants_for_user failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("Test completed successfully!")
        
except Exception as e:
    print(f"Major error: {e}")
    import traceback
    traceback.print_exc()
