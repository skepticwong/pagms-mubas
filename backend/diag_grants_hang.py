
import os
import sys
# Ensure we are in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.grant_service import GrantService
from models import db
import json

print("Checkpoint 1: Starting App")
app = create_app()
with app.app_context():
    print("Checkpoint 2: App Context Loaded")
    try:
        user_id = 1
        print(f"Checkpoint 3: Fetching grants for user {user_id}")
        
        # Manually trace get_grants_for_user logic to see where it hangs
        from models import User, Grant, GrantTeam
        user = User.query.get(user_id)
        print(f"Checkpoint 4: User found: {user.name if user else 'None'}")
        
        grants = Grant.query.filter_by(pi_id=user_id).order_by(Grant.created_at.desc()).all()
        print(f"Checkpoint 5: Found {len(grants)} grants")
        
        for i, grant in enumerate(grants):
            print(f"Tracing Grant {i+1}: {grant.title}")
            
            print("  - Financials...")
            total_spent = sum((cat.spent or 0.0) for cat in grant.categories)
            print("  - Financials DONE")
            
            print("  - Compliance Summary...")
            from services.compliance_service import ComplianceService
            cs = ComplianceService.get_compliance_summary(grant.id, commit=False)
            print("  - Compliance Summary DONE")
            
            print("  - Effort Lock Check...")
            from services.effort_service import EffortService
            el = EffortService.check_spending_lock(grant.id)
            print("  - Effort Lock Check DONE")
            
            print("  - Milestone Completion Rate...")
            # This logic was added recently
            from models import Milestone
            all_milestones = Milestone.query.filter_by(grant_id=grant.id).all()
            completed_milestones = [m for m in all_milestones if m.status == 'completed']
            rate = (len(completed_milestones) / len(all_milestones) * 100) if all_milestones else 0
            print("  - Milestone Completion Rate DONE")
            
            print("  - Assets...")
            # This logic was added/modified recently
            from models import AssetAssignment, Task
            grant_tasks = Task.query.filter_by(grant_id=grant.id).all()
            print(f"    - Found {len(grant_tasks)} tasks")
            # Trace asset assignments
            task_ids = [t.id for t in grant_tasks]
            asset_assignments = AssetAssignment.query.filter(
                AssetAssignment.task_id.in_(task_ids)
            ).all() if task_ids else []
            print(f"    - Found {len(asset_assignments)} asset assignments")
            print("  - Assets DONE")
            
        print("Checkpoint 6: ALL DONE")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
