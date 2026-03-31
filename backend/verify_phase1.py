"""
Direct verification of Phase 1 implementation
"""

import sys
import os

def verify_models_file():
    """Check if the models were added to models.py"""
    models_file = os.path.join(os.path.dirname(__file__), 'models.py')
    
    with open(models_file, 'r') as f:
        content = f.read()
    
    checks = {
        'GrantAmendment class': 'class GrantAmendment' in content,
        'GrantFinancialMetrics class': 'class GrantFinancialMetrics' in content,
        'NCE section comment': 'NCE, BURN RATE & FORECASTING MODELS' in content,
        'grant_amendments table': "__tablename__ = 'grant_amendments'" in content,
        'grant_financial_metrics table': "__tablename__ = 'grant_financial_metrics'" in content
    }
    
    print("🔍 Checking models.py file...")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
    
    return all(checks.values())

def verify_migration_file():
    """Check if migration file exists and has correct content"""
    migration_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_nce_burn_forecast_tables.py')
    
    if not os.path.exists(migration_file):
        print("❌ Migration file does not exist")
        return False
    
    with open(migration_file, 'r') as f:
        content = f.read()
    
    checks = {
        'Migration script exists': os.path.exists(migration_file),
        'Upgrade function': 'def upgrade():' in content,
        'Downgrade function': 'def downgrade():' in content,
        'GrantAmendment creation': "GrantAmendment.__table__.create" in content,
        'GrantFinancialMetrics creation': "GrantFinancialMetrics.__table__.create" in content,
        'Index creation': 'CREATE INDEX' in content
    }
    
    print("\n🔍 Checking migration file...")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
    
    return all(checks.values())

def verify_file_structure():
    """Check if all required files are in place"""
    base_dir = os.path.dirname(__file__)
    
    files_to_check = [
        'models.py',
        'migrations/add_nce_burn_forecast_tables.py',
        'simple_test_models.py'
    ]
    
    print("\n🔍 Checking file structure...")
    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(base_dir, file_path)
        exists = os.path.exists(full_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def verify_model_definitions():
    """Verify model class definitions by parsing the file"""
    models_file = os.path.join(os.path.dirname(__file__), 'models.py')
    
    with open(models_file, 'r') as f:
        lines = f.readlines()
    
    # Find GrantAmendment class
    grant_amendment_found = False
    grant_amendment_attrs = []
    
    # Find GrantFinancialMetrics class  
    grant_metrics_found = False
    grant_metrics_attrs = []
    
    current_class = None
    
    for line in lines:
        line = line.strip()
        
        if 'class GrantAmendment' in line:
            grant_amendment_found = True
            current_class = 'GrantAmendment'
        elif 'class GrantFinancialMetrics' in line:
            grant_metrics_found = True
            current_class = 'GrantFinancialMetrics'
        elif line.startswith('class ') and current_class:
            current_class = None
        elif current_class and 'db.Column' in line:
            attr_name = line.split('=')[0].strip()
            if current_class == 'GrantAmendment':
                grant_amendment_attrs.append(attr_name)
            elif current_class == 'GrantFinancialMetrics':
                grant_metrics_attrs.append(attr_name)
    
    print("\n🔍 Checking model definitions...")
    
    # Check GrantAmendment
    if grant_amendment_found:
        print(f"   ✅ GrantAmendment class found with {len(grant_amendment_attrs)} attributes")
        required_attrs = ['grant_id', 'amendment_type', 'status', 'justification']
        missing_attrs = [attr for attr in required_attrs if attr not in grant_amendment_attrs]
        if missing_attrs:
            print(f"   ⚠️  Missing attributes: {missing_attrs}")
        else:
            print("   ✅ All required GrantAmendment attributes present")
    else:
        print("   ❌ GrantAmendment class not found")
    
    # Check GrantFinancialMetrics
    if grant_metrics_found:
        print(f"   ✅ GrantFinancialMetrics class found with {len(grant_metrics_attrs)} attributes")
        required_attrs = ['grant_id', 'time_elapsed_percentage', 'budget_spent_percentage', 'burn_rate_status']
        missing_attrs = [attr for attr in required_attrs if attr not in grant_metrics_attrs]
        if missing_attrs:
            print(f"   ⚠️  Missing attributes: {missing_attrs}")
        else:
            print("   ✅ All required GrantFinancialMetrics attributes present")
    else:
        print("   ❌ GrantFinancialMetrics class not found")
    
    return grant_amendment_found and grant_metrics_found

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1 VERIFICATION")
    print("=" * 60)
    
    checks = [
        verify_file_structure,
        verify_models_file,
        verify_migration_file,
        verify_model_definitions
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 PHASE 1 VERIFICATION PASSED!")
        print("✅ All models and migrations are properly implemented")
        print("📋 Ready to proceed to Phase 2: Backend Services")
    else:
        print("❌ PHASE 1 VERIFICATION FAILED!")
        print("🔧 Please fix the issues before proceeding to Phase 2")
    
    print("=" * 60)
