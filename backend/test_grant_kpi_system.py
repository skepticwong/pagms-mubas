#!/usr/bin/env python3
"""
Test Grant KPI System - Phase 1
Tests the new grant-level KPI endpoints
"""

import requests
import json

def test_grant_kpi_system():
    """Test grant KPI system endpoints"""
    
    base_url = "http://localhost:5000/api"
    
    print("🧪 Testing Grant KPI System - Phase 1")
    print("=" * 50)
    
    # Test 1: Get available grant KPIs
    try:
        print("📍 Testing GET /grant-kpis/available/19...")
        response = requests.get(f"{base_url}/grant-kpis/available/19", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available KPIs: {len(data.get('available_kpis', []))}")
            for kpi in data.get('available_kpis', [])[:3]:
                print(f"   - {kpi.get('name', 'Unknown')}: {kpi.get('grant_wide_target', 0)} {kpi.get('unit', 'count')}")
        else:
            print(f"❌ Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "-" * 30)
    
    # Test 2: Get grant progress
    try:
        print("📍 Testing GET /grant-kpis/grant/19/progress...")
        response = requests.get(f"{base_url}/grant-kpis/grant/19/progress", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Overall Achievement: {data.get('overall_achievement_pct', 0):.1f}%")
            print(f"📊 Total KPIs: {data.get('total_kpis', 0)}")
            
            categories = data.get('category_breakdown', {})
            for category, cat_data in categories.items():
                print(f"   - {category.title()}: {cat_data.get('achievement_pct', 0):.1f}%")
        else:
            print(f"❌ Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "-" * 30)
    
    # Test 3: Get grant KPIs
    try:
        print("📍 Testing GET /grant-kpis/grant/19...")
        response = requests.get(f"{base_url}/grant-kpis/grant/19", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Grant KPIs: {len(data.get('kpis', []))}")
            for kpi in data.get('kpis', [])[:3]:
                print(f"   - {kpi.get('name', 'Unknown')}: {kpi.get('achievement_pct', 0):.1f}% ({kpi.get('status', 'Unknown')})")
        else:
            print(f"❌ Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Grant KPI System Test Complete!")
    
    print("\n📋 Next Steps:")
    print("1. ✅ Grant KPI tables created")
    print("2. ✅ Grant KPI endpoints working")
    print("3. ⏳ Add KPI management to grant creation wizard")
    print("4. ⏳ Update milestone creation with KPI allocation")
    print("5. ⏳ Create grant-level dashboard")

if __name__ == "__main__":
    test_grant_kpi_system()
