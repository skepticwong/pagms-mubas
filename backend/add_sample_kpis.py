#!/usr/bin/env python3
"""
Add sample KPI data to database for testing
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_sample_kpis():
    """Add sample KPI data for testing"""
    print("🧪 Adding Sample KPI Data")
    print("=" * 50)
    
    try:
        from models import db, Milestone, MilestoneKPI
        
        # Check if there are any milestones
        milestones = Milestone.query.limit(5).all()
        print(f"📊 Found {len(milestones)} milestones")
        
        if not milestones:
            print("⚠️ No milestones found - cannot add KPIs")
            return
        
        # Add sample KPIs to first few milestones
        for milestone in milestones:
            print(f"📈 Adding KPIs to milestone {milestone.id}: {milestone.title}")
            
            # Sample KPI data
            sample_kpis = [
                {
                    'name': 'Beneficiaries Reached',
                    'description': 'Number of beneficiaries directly impacted by milestone activities',
                    'target_value': 100,
                    'unit': 'people',
                    'status': 'ACHIEVED' if milestone.id == 27 else 'PARTIAL'
                },
                {
                    'name': 'Training Sessions Conducted',
                    'description': 'Number of training sessions completed',
                    'target_value': 10,
                    'unit': 'sessions',
                    'status': 'ACHIEVED' if milestone.id == 27 else 'PARTIAL'
                },
                {
                    'name': 'Documentation Delivered',
                    'description': 'Key documentation items delivered',
                    'target_value': 5,
                    'unit': 'documents',
                    'status': 'PARTIAL'
                }
            ]
            
            # Add KPIs to database
            for kpi_data in sample_kpis:
                kpi = MilestoneKPI(
                    milestone_id=milestone.id,
                    name=kpi_data['name'],
                    description=kpi_data['description'],
                    target_value=kpi_data['target_value'],
                    unit=kpi_data['unit'],
                    status=kpi_data['status'],
                    actual_value=kpi_data['target_value'] * 0.85 if kpi_data['status'] == 'PARTIAL' else kpi_data['target_value']
                )
                db.session.add(kpi)
            
            # Commit changes
            db.session.commit()
            print(f"✅ Added {len(sample_kpis)} KPIs to milestone {milestone.id}")
            
        print(f"\n🎉 Successfully added KPIs to {len(milestones)} milestones!")
        print("📊 Total KPIs added:", len(sample_kpis) * len(milestones))
        
    except Exception as e:
        print(f"❌ Error adding sample KPIs: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
    
    print("\n" + "=" * 50)
    print("🎯 Sample KPI Data Addition Complete!")

if __name__ == "__main__":
    add_sample_kpis()
