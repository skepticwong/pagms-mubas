import sqlite3
import os

db_path = os.path.join('backend', 'instance', 'pagms.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 CHECKING SPECIFIC GRANT FOR TRANCHES")
    print("=" * 50)
    
    # Find the grant with code W344FFFFGF
    cursor.execute("SELECT id, grant_code, title, disbursement_type FROM grants WHERE grant_code = 'W344FFFFGF'")
    grant = cursor.fetchone()
    
    if grant:
        grant_id, code, title, disbursement_type = grant
        print(f"Found Grant: {code}")
        print(f"  ID: {grant_id}")
        print(f"  Title: {title}")
        print(f"  Disbursement Type: {disbursement_type}")
        
        # Check tranches for this grant
        cursor.execute("SELECT id, amount, expected_date, status FROM tranches WHERE grant_id = ?", (grant_id,))
        tranches = cursor.fetchall()
        
        print(f"\n💰 Tranches for Grant {grant_id}:")
        if tranches:
            for i, tranche in enumerate(tranches, 1):
                tranche_id, amount, expected_date, status = tranche
                print(f"  Tranche {i}: ${amount:,.2f} (Due: {expected_date}, Status: {status})")
        else:
            print("  ❌ No tranches found!")
    else:
        print("❌ Grant W344FFFFGF not found")
    
    # Also check a few other grants to see if they have tranches
    cursor.execute("SELECT id, grant_code, disbursement_type FROM grants WHERE disbursement_type = 'tranches' LIMIT 5")
    grants = cursor.fetchall()
    
    print(f"\n📊 Checking 5 'tranches' grants:")
    for grant_id, code, disbursement_type in grants:
        cursor.execute("SELECT COUNT(*) FROM tranches WHERE grant_id = ?", (grant_id,))
        tranche_count = cursor.fetchone()[0]
        print(f"  Grant {code} (ID: {grant_id}): {tranche_count} tranches")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
