#!/usr/bin/env python3
"""
Test script to verify the new tranches API endpoint
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import db, Grant, Tranche
from app import create_app

def test_tranche_endpoint():
    app = create_app()
    
    with app.app_context():
        # Check if we have any grants with tranches
        grants = Grant.query.all()
        print(f"Found {len(grants)} grants")
        
        for grant in grants:
            tranches = Tranche.query.filter_by(grant_id=grant.id).all()
            print(f"Grant {grant.id} ({grant.title}): {len(tranches)} tranches")
            
            for tranche in tranches:
                print(f"  - Tranche {tranche.id}: ${tranche.amount} due {tranche.expected_date}")
        
        # Test the API response format
        grant_id = 1
        tranches = Tranche.query.filter_by(grant_id=grant_id).order_by(Tranche.expected_date.asc()).all()
        
        # Format like our API endpoint
        results = []
        for i, tranche in enumerate(tranches):
            d = tranche.to_dict()
            d['tranche_number'] = i + 1
            results.append(d)
        
        print(f"\nAPI Response for Grant {grant_id}:")
        for result in results:
            print(f"  Tranche {result['tranche_number']}: ${result['amount']} (Status: {result['status']})")

if __name__ == '__main__':
    test_tranche_endpoint()
