#!/usr/bin/env python3
"""
Test script to verify GrantKPI model structure
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from models import GrantKPI

def test_grant_kpi():
    app = create_app()
    
    with app.app_context():
        print("=== GrantKPI Model Test ===")
        
        # Check table columns
        print("\nTable columns:")
        for column in GrantKPI.__table__.columns:
            print(f"  {column.name}: {column.type}")
        
        # Check if status column exists
        has_status_column = 'status' in [col.name for col in GrantKPI.__table__.columns]
        print(f"\nHas 'status' column: {has_status_column}")
        
        # Check properties
        properties = []
        for name in dir(GrantKPI):
            attr = getattr(GrantKPI, name)
            if isinstance(attr, property):
                properties.append(name)
        
        print(f"\nProperties: {properties}")
        
        # Try to create a GrantKPI object
        print("\n=== Testing GrantKPI Creation ===")
        try:
            test_kpi = GrantKPI(
                grant_id=1,
                name='Test KPI',
                description='Test description',
                unit='count',
                category='research',
                grant_wide_target=10.0,
                baseline_value=0.0
            )
            print("✅ GrantKPI object created successfully")
            
            # Try to set status (should fail)
            try:
                test_kpi.status = 'active'
                print("❌ Status assignment succeeded (should have failed)")
            except AttributeError as e:
                print(f"✅ Status assignment correctly failed: {e}")
                
        except Exception as e:
            print(f"❌ GrantKPI creation failed: {e}")

if __name__ == '__main__':
    test_grant_kpi()
