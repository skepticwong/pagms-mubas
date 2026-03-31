import sys
import os

# Add backend to path
sys.path.append('backend')
from app import app
from models import db, User, Grant
from services.grant_service_simple import GrantServiceSimple

def test_grant_service():
    with app.app_context():
        # Find a PI
        user = User.query.filter_by(role='PI').first()
        if not user:
            print("No PI user found.")
            return

        print(f"Testing for User ID: {user.id} ({user.name})")
        grants = GrantServiceSimple.get_grants_for_user(user.id)
        
        if not grants:
            print("No grants found for user.")
            return

        for g in grants:
            print(f"Grant: {g['title']}")
            if 'disbursement_type' in g:
                print(f"  ✅ disbursement_type found: {g['disbursement_type']}")
            else:
                print(f"  ❌ disbursement_type MISSING")

if __name__ == "__main__":
    test_grant_service()
