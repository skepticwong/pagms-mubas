#!/usr/bin/env python3
"""
Script to check existing grants in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import db, Grant, User, BudgetCategory, Tranche, Milestone
from app import create_app

def check_existing_grants():
    app = create_app()
    
    with app.app_context():
        print("🔍 CHECKING EXISTING GRANTS IN DATABASE")
        print("=" * 60)
        
        # Get all grants
        grants = Grant.query.all()
        print(f"\n📊 Total Grants Found: {len(grants)}")
        print("=" * 60)
        
        if not grants:
            print("❌ No grants found in the database.")
            return
        
        for i, grant in enumerate(grants, 1):
            print(f"\n🎯 Grant #{i}")
            print(f"   ID: {grant.id}")
            print(f"   Title: {grant.title}")
            print(f"   Grant Code: {grant.grant_code}")
            print(f"   Funder: {grant.funder}")
            print(f"   PI ID: {grant.pi_id}")
            print(f"   Status: {grant.status}")
            print(f"   Total Budget: ${grant.total_budget:,.2f}")
            print(f"   Currency: {grant.currency}")
            print(f"   Exchange Rate: {grant.exchange_rate}")
            print(f"   Disbursement Type: {grant.disbursement_type}")
            print(f"   Start Date: {grant.start_date}")
            print(f"   End Date: {grant.end_date}")
            print(f"   Created: {grant.created_at}")
            
            # Check budget categories
            categories = BudgetCategory.query.filter_by(grant_id=grant.id).all()
            print(f"   📁 Budget Categories: {len(categories)}")
            for cat in categories:
                print(f"      - {cat.name}: ${cat.allocated:,.2f} (Spent: ${cat.spent or 0:,.2f})")
            
            # Check tranches
            tranches = Tranche.query.filter_by(grant_id=grant.id).all()
            print(f"   💰 Tranches: {len(tranches)}")
            for j, tranche in enumerate(tranches, 1):
                print(f"      - Tranche {j}: ${tranche.amount:,.2f} (Due: {tranche.expected_date}, Status: {tranche.status})")
            
            # Check milestones
            milestones = Milestone.query.filter_by(grant_id=grant.id).all()
            print(f"   🎯 Milestones: {len(milestones)}")
            for j, milestone in enumerate(milestones, 1):
                print(f"      - {milestone.title}: {milestone.status} (Due: {milestone.due_date})")
                if milestone.triggers_tranche:
                    print(f"        ↳ Triggers Tranche {milestone.triggers_tranche}")
            
            print("-" * 60)
        
        # Summary statistics
        print(f"\n📈 SUMMARY STATISTICS")
        print("=" * 60)
        print(f"Total Grants: {len(grants)}")
        print(f"Active Grants: {len([g for g in grants if g.status == 'active'])}")
        print(f"Pending Grants: {len([g for g in grants if g.status == 'pending'])}")
        
        # Disbursement types
        disbursement_types = {}
        for grant in grants:
            dt = grant.disbursement_type or 'unknown'
            disbursement_types[dt] = disbursement_types.get(dt, 0) + 1
        
        print(f"\n💰 Disbursement Types:")
        for dt, count in disbursement_types.items():
            print(f"   - {dt}: {count} grants")
        
        # Total budget value
        total_budget = sum(g.total_budget for g in grants)
        print(f"\n💵 Total Portfolio Value: ${total_budget:,.2f}")

if __name__ == '__main__':
    check_existing_grants()
