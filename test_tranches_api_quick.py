#!/usr/bin/env python3
"""
Quick test to check tranches API
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app

def test_tranches_api():
    """Test the tranches API endpoint"""
    app = create_app()
    
    with app.app_context():
        # Import after app context
        from models import Tranche, Grant
        
        print("🔍 Testing Tranches API...")
        
        # Check if any grants exist
        grants = Grant.query.limit(3).all()
        print(f"Found {len(grants)} grants")
        
        if grants:
            for grant in grants:
                print(f"\n📊 Grant {grant.id}: {grant.title}")
                
                # Check tranches for this grant
                tranches = Tranche.query.filter(
                    Tranche.grant_id == grant.id,
                    Tranche.status != 'archived'
                ).all()
                
                print(f"   Found {len(tranches)} tranches:")
                
                for tranche in tranches:
                    try:
                        tranche_dict = tranche.to_dict()
                        print(f"   ✅ Tranche {tranche_dict.get('tranche_number', 'N/A')}: ${tranche_dict.get('amount', 0)} ({tranche_dict.get('status', 'N/A')})")
                        print(f"      Trigger: {tranche_dict.get('trigger_type', 'N/A')}")
                        print(f"      Description: {tranche_dict.get('description', 'N/A')}")
                    except Exception as e:
                        print(f"   ❌ Error with tranche {tranche.id}: {str(e)}")
        
        print("\n✅ API Test Complete!")

if __name__ == '__main__':
    test_tranches_api()
