#!/usr/bin/env python3
"""
Test real KPI data flow from database to frontend
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_real_kpi_data():
    """Test that real KPI data is available and flowing correctly"""
    print("🧪 Testing Real KPI Data Flow")
    print("=" * 50)
    
    try:
        # Test 1: Database connection
        from models import db, Milestone, MilestoneKPI
        print("✅ Database models imported")
        
        # Test 2: Check if KPI tables exist and have data
        total_kpis = MilestoneKPI.query.count()
        print(f"📊 Total KPIs in database: {total_kpis}")
        
        if total_kpis == 0:
            print("⚠️ No KPIs found in database - need to run migration or add sample data")
            return
        
        # Test 3: Check KPIs for specific milestone
        milestone_kpis = MilestoneKPI.query.filter_by(milestone_id=27).all()
        print(f"📈 KPIs for milestone 27: {len(milestone_kpis)}")
        
        for kpi in milestone_kpis:
            print(f"   - {kpi.name}: {kpi.target_value} {kpi.unit}, Status: {kpi.status}")
        
        # Test 4: Test KPI service
        from services.milestone_kpi_service import MilestoneKPIService
        service_kpis = MilestoneKPIService.get_milestone_kpis(27)
        print(f"🔧 Service returned {len(service_kpis)} KPIs")
        
        # Test 5: Test KPI API endpoint
        import requests
        try:
            response = requests.get('http://localhost:5000/api/milestone-kpis/milestone/27', timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"🌐 API returned {len(data.get('kpis', []))} KPIs")
                if data.get('kpis'):
                    for kpi in data['kpis']:
                        print(f"   API - {kpi['name']}: {kpi['target_value']} {kpi['unit']}, Status: {kpi['status']}")
            else:
                print("❌ API returned no KPIs")
        except Exception as e:
            print(f"❌ API test failed: {e}")
        
        # Test 6: Test dashboard endpoint
        try:
            response = requests.get('http://localhost:5000/api/dashboard/milestone/27/impact', timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"📈 Dashboard returned {len(data.get('kpis', []))} KPIs")
                print(f"   Achievement rate: {data.get('summary', {}).get('achievement_rate', 'N/A')}%")
            else:
                print(f"❌ Dashboard returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Dashboard test failed: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 Real KPI Data Test Complete!")

if __name__ == "__main__":
    test_real_kpi_data()
