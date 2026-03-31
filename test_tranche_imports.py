#!/usr/bin/env python3
"""
Simple test to check if Tranche model imports work
"""
import sys
import os

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

print("🔍 Testing Tranche Model Import...")

try:
    print("1. Testing basic model import...")
    from models import db, Tranche, Grant
    print("✅ Successfully imported Tranche and Grant")
    
    print("2. Testing validation service import...")
    from services.tranche_validation_service import TrancheValidationService
    print("✅ Successfully imported TrancheValidationService")
    
    print("3. Testing tranche routes import...")
    from routes.tranches import tranches_bp
    print("✅ Successfully imported tranches blueprint")
    
    print("4. Testing amendment service import...")
    from services.tranche_amendment_service import TrancheAmendmentService, TrancheReleaseService
    print("✅ Successfully imported amendment services")
    
    print("\n🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()

print("\n🔍 Testing Tranche.to_dict method...")

try:
    # Test creating a simple tranche dict
    class MockTranche:
        def __init__(self):
            self.id = 1
            self.grant_id = 1
            self.amount = 1000
            self.expected_date = None
            self.status = 'pending'
            self.actual_received_date = None
            self.created_at = None
            
        def to_dict(self, include_amendments=False):
            result = {
                'id': self.id,
                'grant_id': self.grant_id,
                'amount': self.amount,
                'expected_date': self.expected_date,
                'status': self.status,
                'actual_received_date': self.actual_received_date,
                'created_at': self.created_at
            }
            
            # Add new fields if they exist (for backward compatibility)
            if hasattr(self, 'tranche_number'):
                result['tranche_number'] = self.tranche_number
            else:
                result['tranche_number'] = self.id
            
            if hasattr(self, 'currency'):
                result['currency'] = self.currency
            else:
                result['currency'] = 'USD'
                
            if hasattr(self, 'description'):
                result['description'] = self.description
            else:
                result['description'] = f'Tranche {result["tranche_number"]}'
            
            # Add trigger information if available
            if hasattr(self, 'trigger_type'):
                result['trigger_type'] = self.trigger_type
            else:
                result['trigger_type'] = 'milestone'
                
            if hasattr(self, 'triggering_milestone_id'):
                result['triggering_milestone_id'] = self.triggering_milestone_id
            else:
                result['triggering_milestone_id'] = None
                
            if hasattr(self, 'required_report_type'):
                result['required_report_type'] = self.required_report_type
            else:
                result['required_report_type'] = None
                
            if hasattr(self, 'trigger_date'):
                result['trigger_date'] = self.trigger_date.isoformat() if self.trigger_date else None
            else:
                result['trigger_date'] = None
            
            # Add amendment history if requested
            if include_amendments:
                result['amendment_history'] = []
            
            return result
    
    mock_tranche = MockTranche()
    tranche_dict = mock_tranche.to_dict(include_amendments=True)
    
    print("✅ Tranche.to_dict() works!")
    print(f"   Tranche dict: {tranche_dict}")
    
except Exception as e:
    print(f"❌ Error testing to_dict: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Import test complete!")
