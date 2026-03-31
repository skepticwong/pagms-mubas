import sqlite3
import os
import sys
sys.path.append('backend')

# Test grant 12 directly
db_path = os.path.join('backend', 'instance', 'pagms.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 CHECKING GRANT 12 DATA")
    print("=" * 50)
    
    # Get grant 12 details
    cursor.execute("SELECT id, title, disbursed_funds, exchange_rate, total_budget FROM grants WHERE id = 12")
    grant = cursor.fetchone()
    
    if grant:
        print(f"Grant ID: {grant[0]}")
        print(f"Title: {grant[1]}")
        print(f"Disbursed Funds: {grant[2]} (type: {type(grant[2])})")
        print(f"Exchange Rate: {grant[3]} (type: {type(grant[3])})")
        print(f"Total Budget: {grant[4]}")
        
        # Check budget categories for grant 12
        cursor.execute("SELECT name, allocated, spent FROM budget_categories WHERE grant_id = 12")
        categories = cursor.fetchall()
        
        print(f"\nBudget Categories ({len(categories)}):")
        for cat in categories:
            print(f"  - {cat[0]}: allocated={cat[1]} (type: {type(cat[1])}), spent={cat[2]} (type: {type(cat[2])})")
            
            # Test the problematic calculation
            alloc = cat[1]
            spent = cat[2]
            print(f"    Testing: {alloc} / {spent}")
            if alloc is not None and spent is not None:
                try:
                    burn = (spent / alloc) * 100 if alloc > 0 else 0
                    print(f"    Burn %: {burn}")
                except Exception as e:
                    print(f"    ❌ Error in burn calculation: {e}")
            else:
                print(f"    ⚠️  None values found")
        
        # Test the available disbursed funds calculation
        print(f"\nTesting available disbursed funds calculation:")
        disbursed = grant[2] or 0
        total_spent = sum(cat[2] or 0 for cat in categories)
        available = disbursed - total_spent
        print(f"  Disbursed: {disbursed}")
        print(f"  Total Spent: {total_spent}")
        print(f"  Available: {available}")
        
    else:
        print("❌ Grant 12 not found")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
