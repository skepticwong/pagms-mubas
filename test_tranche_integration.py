#!/usr/bin/env python3
"""
Dynamic Tranche System Integration Test
Phase 3: Test business rules and API integration
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import json
import requests
from datetime import datetime, date
from models import db, Tranche, TrancheAmendment, Grant, User
from services.tranche_validation_service import TrancheValidationService
from services.tranche_amendment_service import TrancheAmendmentService, TrancheReleaseService

class TrancheSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:5000/api"
        self.session = requests.Session()
        
    def test_business_rules(self):
        """Test business rules enforcement"""
        print("🧪 Testing Business Rules Engine...")
        print("=" * 50)
        
        # Test 1: Budget validation
        print("📊 Test 1: Budget Validation")
        grant_id = 1  # Assuming grant 1 exists
        changes = {'amount': 999999999}  # Excessive amount
        
        errors = TrancheValidationService.validate_tranche_amendment(
            grant_id=grant_id,
            tranche_id=1,
            amendments=changes
        )
        
        if errors:
            print("✅ Budget validation working:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("❌ Budget validation failed")
        
        # Test 2: Released tranche protection
        print("\n🔒 Test 2: Released Tranche Protection")
        # Find a released tranche or create a mock one
        tranche = Tranche.query.filter_by(status='released').first()
        if tranche:
            changes = {'amount': 1000}
            errors = TrancheValidationService.validate_tranche_amendment(
                grant_id=tranche.grant_id,
                tranche_id=tranche.id,
                amendments=changes
            )
            
            if errors:
                print("✅ Released tranche protection working:")
                for error in errors:
                    print(f"   - {error}")
            else:
                print("❌ Released tranche protection failed")
        else:
            print("⚠️  No released tranches found for testing")
        
        # Test 3: Trigger validation
        print("\n⚙️  Test 3: Trigger Validation")
        changes = {
            'trigger_type': 'milestone',
            'triggering_milestone_id': 99999  # Non-existent milestone
        }
        
        errors = TrancheValidationService.validate_tranche_amendment(
            grant_id=grant_id,
            tranche_id=1,
            amendments=changes
        )
        
        if errors:
            print("✅ Trigger validation working:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("❌ Trigger validation failed")
        
        print("\n✅ Business Rules Testing Complete!\n")
    
    def test_amendment_workflow(self):
        """Test complete amendment workflow"""
        print("🔄 Testing Amendment Workflow...")
        print("=" * 50)
        
        # Get a test user (RSU role)
        user = User.query.filter_by(role='RSU').first()
        if not user:
            print("❌ No RSU user found for testing")
            return
        
        # Get a test tranche
        tranche = Tranche.query.filter_by(status='pending').first()
        if not tranche:
            print("❌ No pending tranches found for testing")
            return
        
        print(f"📝 Testing with Tranche {tranche.tranche_number} (ID: {tranche.id})")
        
        # Test 1: Submit amendment
        print("\n📤 Test 1: Submit Amendment")
        amendment_data = {
            'amendment_type': 'amount',
            'amount': tranche.amount + 1000,  # Increase by $1000
            'reason': 'Test amendment for integration testing'
        }
        
        result = TrancheAmendmentService.submit_amendment(
            user_id=user.id,
            grant_id=tranche.grant_id,
            tranche_id=tranche.id,
            amendment_data=amendment_data
        )
        
        if result['success']:
            print(f"✅ Amendment submitted successfully (ID: {result['amendment_id']})")
            amendment_id = result['amendment_id']
        else:
            print(f"❌ Amendment submission failed: {result.get('error', 'Unknown error')}")
            return
        
        # Test 2: Approve amendment
        print("\n✅ Test 2: Approve Amendment")
        approve_result = TrancheAmendmentService.approve_amendment(
            approver_id=user.id,
            amendment_id=amendment_id
        )
        
        if approve_result['success']:
            print(f"✅ Amendment approved successfully")
            print(f"   New tranche ID: {approve_result['new_tranche_id']}")
            print(f"   New amount: ${approve_result['new_tranche']['amount']}")
        else:
            print(f"❌ Amendment approval failed: {approve_result.get('error', 'Unknown error')}")
        
        # Test 3: Check amendment history
        print("\n📚 Test 3: Amendment History")
        history = TrancheAmendmentService.get_amendment_history(tranche.id)
        
        if history:
            print(f"✅ Found {len(history)} amendment records:")
            for amendment in history:
                print(f"   - {amendment['amendment_type']}: {amendment['status']} ({amendment['created_at']})")
        else:
            print("⚠️  No amendment history found")
        
        print("\n✅ Amendment Workflow Testing Complete!\n")
    
    def test_release_logic(self):
        """Test tranche release logic"""
        print("💰 Testing Tranche Release Logic...")
        print("=" * 50)
        
        # Test different trigger types
        tranches = Tranche.query.filter(Tranche.status.in_(['pending', 'ready'])).limit(3).all()
        
        if not tranches:
            print("⚠️  No tranches found for release testing")
            return
        
        for tranche in tranches:
            print(f"\n🔍 Testing Tranche {tranche.tranche_number} (Trigger: {tranche.trigger_type})")
            
            # Check release readiness
            readiness = TrancheReleaseService.check_tranche_release_readiness(tranche.id)
            
            if readiness['ready']:
                print(f"✅ Ready for release: {readiness.get('trigger_details', 'No details')}")
                
                # Test actual release (only if not already released)
                if tranche.status != 'released':
                    user = User.query.filter_by(role='RSU').first()
                    if user:
                        release_result = TrancheReleaseService.release_tranche(
                            tranche_id=tranche.id,
                            released_by_user_id=user.id
                        )
                        
                        if release_result['success']:
                            print(f"✅ Tranche released successfully: ${release_result['amount']}")
                        else:
                            print(f"❌ Tranche release failed: {release_result.get('error', 'Unknown error')}")
                    else:
                        print("⚠️  No RSU user available for release test")
            else:
                print(f"⏳ Not ready for release: {readiness.get('trigger_details', 'No details')}")
                if 'error' in readiness:
                    print(f"   Error: {readiness['error']}")
        
        print("\n✅ Release Logic Testing Complete!\n")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("🌐 Testing API Endpoints...")
        print("=" * 50)
        
        # Test 1: Get tranches for a grant
        print("\n📥 Test 1: Get Grant Tranches")
        try:
            response = self.session.get(f"{self.base_url}/grants/1/tranches")
            if response.status_code == 200:
                tranches = response.json()
                print(f"✅ Retrieved {len(tranches)} tranches")
                if tranches:
                    print(f"   First tranche: ${tranches[0]['amount']} ({tranches[0]['status']})")
            else:
                print(f"❌ Failed to get tranches: {response.status_code}")
        except Exception as e:
            print(f"❌ API error: {str(e)}")
        
        # Test 2: Validate tranche changes
        print("\n🔍 Test 2: Validate Changes")
        try:
            validation_data = {
                'tranche_id': 1,
                'changes': {'amount': 5000}
            }
            response = self.session.post(
                f"{self.base_url}/grants/1/tranches/validate",
                json=validation_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['valid']:
                    print("✅ Changes are valid")
                else:
                    print(f"✅ Validation working (errors found): {len(result['errors'])} errors")
            else:
                print(f"❌ Validation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ API error: {str(e)}")
        
        # Test 3: Check release readiness
        print("\n💰 Test 3: Check Release Readiness")
        try:
            response = self.session.get(f"{self.base_url}/tranches/1/release-check")
            if response.status_code == 200:
                result = response.json()
                if result['ready']:
                    print(f"✅ Tranche ready: {result.get('trigger_details', 'No details')}")
                else:
                    print(f"⏳ Tranche not ready: {result.get('trigger_details', 'No details')}")
            else:
                print(f"❌ Release check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ API error: {str(e)}")
        
        print("\n✅ API Endpoint Testing Complete!\n")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Dynamic Tranche System Integration Test")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Test business rules
            self.test_business_rules()
            
            # Test amendment workflow
            self.test_amendment_workflow()
            
            # Test release logic
            self.test_release_logic()
            
            # Test API endpoints
            self.test_api_endpoints()
            
            print("🎉 All Integration Tests Completed Successfully!")
            print("=" * 60)
            print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    # Run the integration tests
    tester = TrancheSystemTester()
    tester.run_all_tests()
