#!/usr/bin/env python3
"""
Test script to debug the tranches API for grant W344FFFFGF
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import db, Grant, Tranche
from app import create_app
import json

def test_tranches_api():
    app = create_app()
    
    with app.app_context():
        print("🔍 TESTING TRANCHES API FOR W344FFFFGF")
        print("=" * 60)
        
        # Find the grant
        grant = Grant.query.filter_by(grant_code='W344FFFFGF').first()
        if not grant:
            print("❌ Grant W344FFFFGF not found")
            return
        
        print(f"✅ Found Grant: {grant.title}")
        print(f"   ID: {grant.id}")
        print(f"   Disbursement Type: {grant.disbursement_type}")
        
        # Get tranches for this grant
        tranches = Tranche.query.filter_by(grant_id=grant.id).order_by(Tranche.expected_date.asc()).all()
        
        print(f"\n💰 Tranches in Database ({len(tranches)}):")
        for i, tranche in enumerate(tranches, 1):
            print(f"   Tranche {i}: ${tranche.amount:,.2f} (Due: {tranche.expected_date}, Status: {tranche.status})")
        
        # Test the API response format
        print(f"\n📡 Testing API Response Format:")
        api_response = []
        for i, tranche in enumerate(tranches):
            tranche_dict = tranche.to_dict()
            tranche_dict['tranche_number'] = i + 1  # Add 1-based numbering
            api_response.append(tranche_dict)
        
        print(f"   API Response:")
        for tranche_data in api_response:
            print(f"   - ID: {tranche_data['id']}")
            print(f"     tranche_number: {tranche_data['tranche_number']}")
            print(f"     amount: {tranche_data['amount']}")
            print(f"     expected_date: {tranche_data['expected_date']}")
            print(f"     status: {tranche_data['status']}")
        
        # Test JSON serialization
        try:
            json_str = json.dumps(api_response, default=str)
            print(f"\n✅ JSON serialization successful")
            print(f"   Response length: {len(json_str)} characters")
        except Exception as e:
            print(f"\n❌ JSON serialization failed: {e}")
        
        # Test specific grant ID
        print(f"\n🎯 Testing with Grant ID: {grant.id}")
        print(f"   API Endpoint: /api/grants/{grant.id}/tranches")
        print(f"   Expected Response: {len(api_response)} tranches")

if __name__ == '__main__':
    test_tranches_api()
