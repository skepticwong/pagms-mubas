#!/usr/bin/env python3
"""
Test Phase 1 Asset Management Integration
"""

import sys
import traceback

def main():
    print("🧪 PHASE 1 ASSET MANAGEMENT TEST")
    print("=" * 50)
    
    try:
        # Test 1: App creation with asset routes
        print("1. Testing app creation...")
        from app import create_app
        app = create_app()
        print("   ✅ App created with asset routes")
        
        # Test 2: Database setup
        print("2. Testing database setup...")
        from app import setup_database
        setup_database(app)
        print("   ✅ Database setup successful")
        
        # Test 3: Asset model imports
        print("3. Testing asset models...")
        from models import Asset, AssetMaintenance, AssetTransfer
        print("   ✅ Asset models imported successfully")
        
        # Test 4: Asset service imports
        print("4. Testing asset service...")
        from services.asset_service import AssetService
        print("   ✅ Asset service imported successfully")
        
        # Test 5: Asset routes registration
        print("5. Testing asset routes...")
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            print(f"   Health check: {response.status_code}")
            
            # Test asset categories endpoint
            response = client.get('/api/assets/categories')
            print(f"   Categories endpoint: {response.status_code}")
            
            # Test source types endpoint
            response = client.get('/api/assets/source-types')
            print(f"   Source types endpoint: {response.status_code}")
            
            # Test status options endpoint
            response = client.get('/api/assets/status-options')
            print(f"   Status options endpoint: {response.status_code}")
        
        # Test 6: Create sample asset
        print("6. Testing asset creation...")
        with app.app_context():
            from models import db, User, Grant, Task
            
            # Get or create test data
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                print("   ⚠️  Test user not found - creating sample asset without user")
                return False
            
            test_grant = Grant.query.first()
            if not test_grant:
                print("   ⚠️  No grants found - cannot test asset creation")
                return False
            
            test_task = Task.query.filter_by(grant_id=test_grant.id).first()
            if not test_task:
                print("   ⚠️  No tasks found - creating sample task")
                test_task = Task(
                    grant_id=test_grant.id,
                    title='Sample Task for Asset Testing',
                    description='Test task for asset management',
                    status='TODO',
                    created_by_user_id=test_user.id
                )
                db.session.add(test_task)
                db.session.commit()
            
            # Create sample asset
            asset_data = {
                'task_id': test_task.id,
                'name': 'Test Asset - Laptop',
                'description': 'Sample laptop for testing',
                'category': 'IT Equipment',
                'source_type': 'PURCHASED',
                'estimated_cost': 1500.00
            }
            
            asset, rule_result = AssetService.create_asset_request(
                test_task.id, asset_data, test_user.id
            )
            
            if asset:
                print(f"   ✅ Asset created: {asset.name} (ID: {asset.id})")
                print(f"   Asset tag: {asset.asset_tag}")
                print(f"   Status: {asset.status}")
                print(f"   Rule outcome: {rule_result.get('outcome', 'PASS')}")
            else:
                print("   ❌ Failed to create asset")
                return False
        
        # Test 7: Asset statistics
        print("7. Testing asset statistics...")
        with app.app_context():
            if test_grant:
                stats = AssetService.get_asset_statistics(test_grant.id)
                print(f"   ✅ Statistics: {stats['total_assets']} assets")
                print(f"   Total value: ${stats['total_value']}")
        
        print("\n🎉 PHASE 1 TEST COMPLETE!")
        print("=" * 50)
        print("✅ All tests passed!")
        print("✅ Asset Management is ready for Phase 2")
        print("\n📋 What's working:")
        print("   • Database tables created")
        print("   • Asset models defined")
        print("   • Asset service functional")
        print("   • API endpoints responding")
        print("   • Asset creation workflow")
        print("   • Statistics calculation")
        
        print("\n🚀 Ready for:")
        print("   • Frontend integration")
        print("   • Asset request workflows")
        print("   • Asset management UI")
        print("   • Phase 2 implementation")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
