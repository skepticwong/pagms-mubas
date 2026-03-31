#!/usr/bin/env python3
"""
Debug script to identify the exact location of the division error
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import db, Grant
from app import create_app
from services.report_service import ReportService

def debug_report_generation(grant_id):
    app = create_app()
    
    with app.app_context():
        print(f"🔍 DEBUGGING REPORT GENERATION FOR GRANT {grant_id}")
        print("=" * 60)
        
        try:
            # Step 1: Get the grant
            print("1. Getting grant...")
            grant = Grant.query.get(grant_id)
            if not grant:
                print("❌ Grant not found")
                return
            print(f"✅ Grant found: {grant.title}")
            
            # Step 2: Test grant.to_dict() - this is likely where it fails
            print("\n2. Testing grant.to_dict()...")
            try:
                grant_dict = grant.to_dict(include_categories=True)
                print("✅ grant.to_dict() successful")
                print(f"   - Disbursed funds: {grant_dict.get('disbursed_funds')}")
                print(f"   - Available disbursed: {grant_dict.get('available_disbursed_funds')}")
                print(f"   - Progress %: {grant_dict.get('project_progress_percentage')}")
                print(f"   - Exchange rate: {grant_dict.get('exchange_rate')}")
                print(f"   - Categories count: {len(grant_dict.get('categories', []))}")
                
                # Check each category for None values
                for i, cat in enumerate(grant_dict.get('categories', [])):
                    print(f"   - Category {i}: {cat.get('name')} - Allocated: {cat.get('allocated')}, Spent: {cat.get('spent')}")
                    
            except Exception as e:
                print(f"❌ grant.to_dict() failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return
            
            # Step 3: Test compile_report_data
            print("\n3. Testing compile_report_data...")
            try:
                report_data = ReportService.compile_report_data(grant_id, "Annual", "2024")
                print("✅ compile_report_data successful")
                print(f"   - Report data keys: {list(report_data.keys())}")
                
                # Check grant data in report
                grant_data = report_data.get('grant', {})
                print(f"   - Grant exchange rate: {grant_data.get('exchange_rate')}")
                print(f"   - Grant progress %: {grant_data.get('project_progress_percentage')}")
                
            except Exception as e:
                print(f"❌ compile_report_data failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return
            
            # Step 4: Test PDF generation
            print("\n4. Testing PDF generation...")
            try:
                filename = f"debug_report_{grant_id}.pdf"
                filepath = os.path.join('backend', 'uploads', 'reports', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                ReportService.generate_pdf_report(report_data, filepath)
                print(f"✅ PDF generation successful: {filepath}")
                
            except Exception as e:
                print(f"❌ PDF generation failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    # Test with grant ID 12 (from the error)
    debug_report_generation(12)
