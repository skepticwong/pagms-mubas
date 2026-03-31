#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from models import db, Grant, User

def main():
    app = create_app()
    with app.app_context():
        try:
            grant_count = Grant.query.count()
            user_count = User.query.count()
            print(f"Users in DB: {user_count}")
            print(f"Grants in DB: {grant_count}")
            
            if grant_count > 0:
                first_grant = Grant.query.first()
                print(f"First grant: {first_grant.title} (PI ID: {first_grant.pi_id})")
            
            # Check all users
            users = User.query.all()
            for u in users:
                print(f"User: {u.id}, {u.email}, {u.role}")
                
            # Test grants query directly
            print("\nTesting grants query...")
            grants = Grant.query.all()
            print(f"Found {len(grants)} grants")
            for g in grants:
                print(f"Grant: {g.title} - PI: {g.pi_id} - Status: {g.status}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
