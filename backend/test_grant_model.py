#!/usr/bin/env python3
"""
Isolated test to check if the Grant model works
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_grant_model():
    """Test the Grant model directly"""
    
    print("🧪 Testing Grant Model Directly")
    print("=" * 40)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from models import db, Grant, User, FunderProfile
            
            print("✅ Models imported successfully")
            
            # Test database connection
            try:
                grants = Grant.query.all()
                print(f"✅ Grant query successful: {len(grants)} grants found")
                
                if grants:
                    grant = grants[0]
                    print(f"  First grant: {grant.grant_code}")
                    print(f"  Funder ID: {grant.funder_id}")
                    print(f"  PI ID: {grant.pi_id}")
                    
                    # Test accessing funder relationship
                    try:
                        if hasattr(grant, 'funder_profile') and grant.funder_profile:
                            print(f"  Funder: {grant.funder_profile.name}")
                        else:
                            print("  No funder relationship or funder is None")
                    except Exception as e:
                        print(f"  Funder relationship error: {e}")
                else:
                    print("  No grants found in database")
                
            except Exception as e:
                print(f"❌ Grant query failed: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # Test User query
            try:
                users = User.query.all()
                print(f"✅ User query successful: {len(users)} users found")
                
                if users:
                    user = users[0]
                    print(f"  First user: {user.name} ({user.email})")
                    
                    # Test grants for this user
                    try:
                        user_grants = Grant.query.filter_by(pi_id=user.id).all()
                        print(f"  Grants for user {user.id}: {len(user_grants)}")
                        
                        if user_grants:
                            print(f"  First user grant: {user_grants[0].grant_code}")
                        else:
                            print("  No grants for this user")
                            
                    except Exception as e:
                        print(f"  ❌ User grants query failed: {e}")
                        import traceback
                        traceback.print_exc()
                        return False
                        
            except Exception as e:
                print(f"❌ User query failed: {e}")
                return False
            
            print("\n✅ All model tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_grant_model()
    if not success:
        exit(1)
