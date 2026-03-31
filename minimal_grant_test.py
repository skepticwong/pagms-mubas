#!/usr/bin/env python3
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

print("=== MINIMAL GRANT TEST ===")

try:
    # Test basic imports
    print("1. Testing imports...")
    from flask import Flask
    from models import db, User, Grant, GrantTeam
    print("   ✓ Basic imports successful")
    
    # Create app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'pagms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        print("2. Testing database connection...")
        
        # Test User query
        user_count = User.query.count()
        print(f"   Users in DB: {user_count}")
        
        # Test Grant query
        grant_count = Grant.query.count()
        print(f"   Grants in DB: {grant_count}")
        
        # Test GrantTeam query
        team_count = GrantTeam.query.count()
        print(f"   Grant teams in DB: {team_count}")
        
        if user_count > 0:
            print("3. Testing user access...")
            test_user = User.query.first()
            print(f"   Test user: {test_user.name} (ID: {test_user.id}, Role: {test_user.role})")
            
            # Test the specific query that's failing
            print("4. Testing grant query...")
            if test_user.role == 'RSU':
                grants = Grant.query.order_by(Grant.created_at.desc()).all()
                print(f"   RSU grants query: {len(grants)} grants")
            elif test_user.role == 'PI':
                grants = Grant.query.filter_by(pi_id=test_user.id).all()
                print(f"   PI grants query: {len(grants)} grants")
                
                # Test GrantTeam query
                team_grants = GrantTeam.query.filter_by(user_id=test_user.id, role='Co-PI').all()
                print(f"   Team grants: {len(team_grants)}")
                
                # Test the problematic or_ query
                from sqlalchemy import or_
                team_grants_ids = [gt.grant_id for gt in team_grants]
                combined_grants = Grant.query.filter(
                    or_(Grant.pi_id == test_user.id, Grant.id.in_(team_grants_ids))
                ).all()
                print(f"   Combined grants query: {len(combined_grants)} grants")
        
        print("✓ All tests passed!")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
