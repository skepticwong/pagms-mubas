import sys
import os
sys.path.append('backend')

from models import db, Grant, BudgetCategory, Tranche, Milestone
from app import create_app

app = create_app()

with app.app_context():
    grants = Grant.query.all()
    print(f"Found {len(grants)} grants:")
    
    for grant in grants:
        print(f"\nGrant: {grant.title}")
        print(f"  Code: {grant.grant_code}")
        print(f"  Status: {grant.status}")
        print(f"  Budget: ${grant.total_budget}")
        print(f"  Disbursement: {grant.disbursement_type}")
        
        tranches = Tranche.query.filter_by(grant_id=grant.id).all()
        print(f"  Tranches: {len(tranches)}")
        
        milestones = Milestone.query.filter_by(grant_id=grant.id).all()
        print(f"  Milestones: {len(milestones)}")
