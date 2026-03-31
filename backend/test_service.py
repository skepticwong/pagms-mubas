#!/usr/bin/env python3
"""
Minimal test for dashboard service
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_service():
    """Test the dashboard service directly"""
    print("🧪 Testing Dashboard Service Directly")
    print("=" * 50)
    
    try:
        # Test database connection
        from models import db, Milestone
        print("✅ Database models imported")
        
        # Check if milestone 27 exists
        milestone = Milestone.query.get(27)
        if milestone:
            print(f"✅ Milestone 27 found: {milestone.title}")
        else:
            print("❌ Milestone 27 not found")
            milestones = Milestone.query.limit(5).all()
            print(f"Available milestones: {[m.id for m in milestones]}")
            return
        
        # Test dashboard service
        from services.milestone_dashboard_service import MilestoneDashboardService
        print("✅ Dashboard service imported")
        
        # Test impact scorecard
        print("\n📊 Testing Impact Scorecard...")
        scorecard = MilestoneDashboardService.get_milestone_impact_scorecard(27)
        if scorecard:
            print("✅ Impact scorecard generated")
            print(f"   Title: {scorecard.get('milestone_info', {}).get('title', 'N/A')}")
            print(f"   KPIs: {len(scorecard.get('kpis', []))}")
        else:
            print("❌ Impact scorecard failed")
        
        # Test operational metrics
        print("\n⚙️ Testing Operational Metrics...")
        metrics = MilestoneDashboardService.get_milestone_operational_metrics(27)
        if metrics:
            print("✅ Operational metrics generated")
            print(f"   Asset integrity: {metrics.get('asset_integrity', {}).get('return_rate', 'N/A')}%")
        else:
            print("❌ Operational metrics failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_service()
