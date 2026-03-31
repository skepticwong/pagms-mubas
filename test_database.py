#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from models import db, Grant, User, BudgetCategory, Milestone

def main():
    app = create_app()
    with app.app_context():
        try:
            print("=== DATABASE VERIFICATION ===")
            
            # Check users
            users = User.query.all()
            print(f"Total users: {len(users)}")
            for user in users:
                print(f"  - {user.name} ({user.email}) - Role: {user.role}")
            
            # Check grants
            grants = Grant.query.all()
            print(f"\nTotal grants: {len(grants)}")
            for grant in grants:
                print(f"  - {grant.title} - PI ID: {grant.pi_id} - Status: {grant.status}")
                
                # Check budget categories for this grant
                categories = BudgetCategory.query.filter_by(grant_id=grant.id).all()
                print(f"    Budget categories: {len(categories)}")
                for cat in categories:
                    print(f"      - {cat.name}: ${cat.allocated} (spent: ${cat.spent})")
                
                # Check milestones for this grant
                milestones = Milestone.query.filter_by(grant_id=grant.id).all()
                print(f"    Milestones: {len(milestones)}")
                for milestone in milestones:
                    print(f"      - {milestone.title}: {milestone.status} (due: {milestone.due_date})")
            
            # Test specific user access
            print("\n=== USER ACCESS TEST ===")
            if users:
                test_user = users[0]  # Test first user
                print(f"Testing access for user: {test_user.name} ({test_user.role})")
                
                # Test GrantService.get_grants_for_user
                from services.grant_service import GrantService
                try:
                    user_grants = GrantService.get_grants_for_user(test_user.id)
                    print(f"  Grants accessible: {len(user_grants)}")
                    for g in user_grants:
                        print(f"    - {g['title']} (Role: {g.get('user_role', 'Unknown')})")
                except Exception as e:
                    print(f"  Error getting grants for user: {e}")
                    import traceback
                    traceback.print_exc()
            
            print("\n=== DATABASE STATUS: OK ===")
            
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
