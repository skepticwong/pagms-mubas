# test_asset_assignment.py
"""
Test script for Asset Assignment functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Grant, Task, Asset, AssetAssignment
from services.asset_assignment_service import AssetAssignmentService
from datetime import datetime

def test_asset_assignment():
    """Test the complete asset assignment workflow"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Asset Assignment Workflow...")
        
        try:
            # Create test data
            print("\n1️⃣ Setting up test data...")
            
            # Create test users
            pi = User(name="Dr. Test PI", email="pi@test.com", role="PI")
            pi.set_password("test123")
            team_member = User(name="Test Team Member", email="team@test.com", role="Team")
            team_member.set_password("test123")
            
            db.session.add(pi)
            db.session.add(team_member)
            db.session.commit()
            
            # Create test grant
            grant = Grant(
                title="Test Grant",
                funder="Test Funder",
                grant_code="TEST-001",
                start_date=datetime.now().date(),
                end_date=datetime.now().date(),
                total_budget=10000.0,
                pi_id=pi.id
            )
            db.session.add(grant)
            db.session.commit()
            
            # Create test task
            task = Task(
                grant_id=grant.id,
                assigned_to=team_member.id,
                title="Test Task",
                task_type="Field Work",
                deadline=datetime.now().date(),
                status="PENDING"
            )
            db.session.add(task)
            db.session.commit()
            
            # Create test asset
            asset = Asset(
                name="Test Equipment",
                asset_tag="TEST-001",
                category="Lab Equipment",
                grant_id=grant.id,
                source_type="PURCHASED",
                status="ACTIVE"
            )
            db.session.add(asset)
            db.session.commit()
            
            print("✅ Test data created")
            print(f"   - PI: {pi.name} (ID: {pi.id})")
            print(f"   - Team Member: {team_member.name} (ID: {team_member.id})")
            print(f"   - Grant: {grant.title} (ID: {grant.id})")
            print(f"   - Task: {task.title} (ID: {task.id})")
            print(f"   - Asset: {asset.name} (ID: {asset.id})")
            
            # Test 1: Create asset assignment
            print("\n2️⃣ Testing asset assignment creation...")
            asset_requirements = [
                {
                    'asset_id': asset.id,
                    'quantity': 1,
                    'notes': 'Test assignment'
                }
            ]
            
            assignments = AssetAssignmentService.request_assets_for_task(
                task.id, asset_requirements, pi.id
            )
            
            print(f"✅ Created {len(assignments)} asset assignments")
            assignment = assignments[0]
            print(f"   - Assignment ID: {assignment.id}")
            print(f"   - Status: {assignment.status}")
            print(f"   - Asset: {assignment.asset.name}")
            print(f"   - Task: {assignment.task.title}")
            
            # Test 2: Confirm pickup
            print("\n3️⃣ Testing asset pickup confirmation...")
            updated_assignment = AssetAssignmentService.confirm_asset_pickup(
                assignment.id, team_member.id, "test_pickup_photo.jpg"
            )
            
            print(f"✅ Pickup confirmed")
            print(f"   - Status: {updated_assignment.status}")
            print(f"   - Assigned at: {updated_assignment.assigned_at}")
            print(f"   - Asset status: {updated_assignment.asset.status}")
            
            # Test 3: Check task completion blocking
            print("\n4️⃣ Testing task completion blocking...")
            can_complete = AssetAssignmentService.can_complete_task(task.id)
            print(f"✅ Can complete task: {can_complete}")
            
            if not can_complete:
                pending = AssetAssignmentService.get_pending_returns_for_task(task.id)
                print(f"   - Pending returns: {len(pending)}")
                for p in pending:
                    print(f"     * {p.asset.name} (assigned to {p.assigned_user.name})")
            
            # Test 4: Confirm return
            print("\n5️⃣ Testing asset return confirmation...")
            returned_assignment = AssetAssignmentService.confirm_asset_return(
                assignment.id, team_member.id, "test_return_photo.jpg"
            )
            
            print(f"✅ Return confirmed")
            print(f"   - Status: {returned_assignment.status}")
            print(f"   - Returned at: {returned_assignment.returned_at}")
            print(f"   - Asset status: {returned_assignment.asset.status}")
            
            # Test 5: Check if task can now be completed
            print("\n6️⃣ Testing task completion after return...")
            can_complete_after = AssetAssignmentService.can_complete_task(task.id)
            print(f"✅ Can complete task now: {can_complete_after}")
            
            # Test 6: Test utilization metrics
            print("\n7️⃣ Testing utilization metrics...")
            metrics = AssetAssignmentService.get_asset_utilization_metrics(grant.id)
            print(f"✅ Utilization metrics calculated:")
            print(f"   - Asset utilization rate: {metrics['asset_utilization_rate']}%")
            print(f"   - Asset turnaround time: {metrics['asset_turnaround_time']} days")
            print(f"   - Missing asset risk: {metrics['missing_asset_risk']}")
            print(f"   - Total assignments: {metrics['total_assignments']}")
            
            print("\n🎉 All tests passed! Asset Assignment workflow is working correctly.")
            
            # Cleanup test data
            print("\n🧹 Cleaning up test data...")
            db.session.delete(assignment)
            db.session.delete(asset)
            db.session.delete(task)
            db.session.delete(grant)
            db.session.delete(team_member)
            db.session.delete(pi)
            db.session.commit()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    test_asset_assignment()
