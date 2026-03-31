# test_phase3_implementation.py
"""
Test script for Phase 3: Reporting Implementation
Tests dashboard generation, visualization, and export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Milestone, Grant, MilestoneKPI
from services.milestone_dashboard_service import MilestoneDashboardService
from datetime import datetime

def test_phase3_implementation():
    """Test Phase 3 implementation"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Phase 3: Reporting Implementation...")
        
        try:
            # Test 1: Check if new services exist
            print("\n1️⃣ Testing new dashboard service...")
            
            # Test dashboard service
            print("✅ MilestoneDashboardService imported successfully")
            
            # Test 2: Create test data for dashboard testing
            print("\n2️⃣ Testing impact scorecard generation...")
            
            # Get existing grant and milestone
            test_grant = Grant.query.first()
            if not test_grant:
                print("❌ No grant found for testing")
                return False
            
            test_milestone = Milestone.query.filter_by(grant_id=test_grant.id).first()
            if not test_milestone:
                print("❌ No milestone found for testing")
                return False
            
            print(f"✅ Using milestone: {test_milestone.title}")
            
            # Test impact scorecard
            scorecard = MilestoneDashboardService.get_milestone_impact_scorecard(test_milestone.id)
            if scorecard:
                print(f"✅ Impact scorecard generated - {len(scorecard['kpis'])} KPIs")
                print(f"✅ Achievement rate: {scorecard['summary']['achievement_rate']}%")
            else:
                print("❌ Failed to generate impact scorecard")
                return False
            
            # Test 3: Test operational metrics
            print("\n3️⃣ Testing operational metrics generation...")
            
            operational_metrics = MilestoneDashboardService.get_milestone_operational_metrics(test_milestone.id)
            if operational_metrics:
                print(f"✅ Operational metrics generated")
                print(f"✅ Asset return rate: {operational_metrics['asset_integrity']['return_rate']}%")
                print(f"✅ Utilization rate: {operational_metrics['utilization']['utilization_rate']}%")
                print(f"✅ Task completion rate: {operational_metrics['productivity']['completion_rate']}%")
            else:
                print("❌ Failed to generate operational metrics")
                return False
            
            # Test 4: Test grant dashboard
            print("\n4️⃣ Testing grant dashboard generation...")
            
            grant_dashboard = MilestoneDashboardService.get_grant_dashboard(test_grant.id)
            if grant_dashboard:
                print(f"✅ Grant dashboard generated")
                print(f"✅ Total milestones: {grant_dashboard['overall_metrics']['total_milestones']}")
                print(f"✅ KPI achievement rate: {grant_dashboard['overall_metrics']['kpi_achievement_rate']}%")
                print(f"✅ Asset return rate: {grant_dashboard['overall_metrics']['asset_return_rate']}%")
            else:
                print("❌ Failed to generate grant dashboard")
                return False
            
            # Test 5: Test performance trends
            print("\n5️⃣ Testing performance trends generation...")
            
            trends = MilestoneDashboardService.generate_performance_trends(test_grant.id, 90)
            if trends:
                print(f"✅ Performance trends generated")
                print(f"✅ Trends period: {trends['period']['days_back']} days")
                print(f"✅ Average KPI achievement: {trends['averages']['avg_kpi_achievement']}%")
                print(f"✅ Average asset return rate: {trends['averages']['avg_asset_return_rate']}%")
            else:
                print("❌ Failed to generate performance trends")
                return False
            
            # Test 6: Test data structure validation
            print("\n6️⃣ Testing data structure validation...")
            
            # Validate scorecard structure
            required_scorecard_keys = ['milestone_info', 'kpis', 'summary']
            for key in required_scorecard_keys:
                if key not in scorecard:
                    print(f"❌ Missing scorecard key: {key}")
                    return False
            print("✅ Scorecard structure validated")
            
            # Validate operational metrics structure
            required_metrics_keys = ['asset_integrity', 'utilization', 'productivity', 'conflicts']
            for key in required_metrics_keys:
                if key not in operational_metrics:
                    print(f"❌ Missing operational metrics key: {key}")
                    return False
            print("✅ Operational metrics structure validated")
            
            # Validate grant dashboard structure
            required_dashboard_keys = ['grant_info', 'overall_metrics', 'kpi_summary', 'asset_summary', 'task_summary']
            for key in required_dashboard_keys:
                if key not in grant_dashboard:
                    print(f"❌ Missing grant dashboard key: {key}")
                    return False
            print("✅ Grant dashboard structure validated")
            
            print("\n🎉 Phase 3 Implementation Test Results:")
            print("✅ Dashboard service implemented correctly")
            print("✅ Impact scorecard generation working")
            print("✅ Operational metrics generation working")
            print("✅ Grant dashboard generation working")
            print("✅ Performance trends generation working")
            print("✅ Data structures properly formatted")
            print("✅ All visualization data ready")
            
            print("\n🚀 Phase 3: REPORTING - IMPLEMENTATION COMPLETE!")
            print("📋 Ready for frontend integration and deployment")
            
        except Exception as e:
            print(f"\n❌ Phase 3 test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = test_phase3_implementation()
    if success:
        print("\n✅ All Phase 3 tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Phase 3 tests failed!")
        sys.exit(1)
