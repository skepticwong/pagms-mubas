#!/usr/bin/env python3
"""
Isolated test for dashboard components
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_operational_metrics():
    """Test operational metrics step by step"""
    print("🧪 Testing Operational Metrics Components")
    print("=" * 50)
    
    try:
        # Test 1: Database connection
        from models import db, Milestone, Task, AssetAssignment
        print("✅ Database models imported")
        
        # Test 2: Get milestone
        milestone = Milestone.query.get(27)
        if milestone:
            print(f"✅ Milestone 27 found: {milestone.title}")
        else:
            print("❌ Milestone 27 not found")
            return
        
        # Test 3: Get tasks for milestone
        tasks = Task.query.filter_by(milestone_id=27).all()
        print(f"✅ Found {len(tasks)} tasks for milestone 27")
        
        # Test 4: Get asset assignments
        all_assignments = []
        for task in tasks:
            assignments = AssetAssignment.query.filter_by(task_id=task.id).all()
            all_assignments.extend(assignments)
        
        print(f"✅ Found {len(all_assignments)} asset assignments")
        
        # Test 5: Test AssetAssignmentService
        from services.asset_assignment_service import AssetAssignmentService
        milestone_assets = AssetAssignmentService.get_milestone_assets(27)
        print(f"✅ AssetAssignmentService returned {len(milestone_assets)} assets")
        
        # Test 6: Test conflict service
        from services.asset_conflict_service import AssetConflictService
        conflicts = AssetConflictService.check_asset_conflicts(27, milestone.due_date, milestone.completion_date)
        print(f"✅ Conflict service returned {len(conflicts)} conflicts")
        
        # Test 7: Test full operational metrics
        from services.milestone_dashboard_service import MilestoneDashboardService
        metrics = MilestoneDashboardService.get_milestone_operational_metrics(27)
        if metrics:
            print("✅ Full operational metrics generated successfully")
            print(f"   Asset integrity: {metrics.get('asset_integrity', {}).get('return_rate', 'N/A')}%")
            print(f"   Utilization: {metrics.get('utilization', {}).get('utilization_rate', 'N/A')}%")
        else:
            print("❌ Full operational metrics failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_operational_metrics()
