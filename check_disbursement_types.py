import sqlite3
import os

db_path = os.path.join('backend', 'instance', 'pagms.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 CHECKING DISBURSEMENT TYPES AND TRANCHES")
    print("=" * 60)
    
    # Get all grants with their disbursement types and tranche counts
    cursor.execute("""
        SELECT g.id, g.grant_code, g.title, g.disbursement_type, 
               COUNT(t.id) as tranche_count
        FROM grants g 
        LEFT JOIN tranches t ON g.id = t.grant_id 
        GROUP BY g.id
        ORDER BY g.id
    """)
    
    grants = cursor.fetchall()
    
    print(f"\n📊 Grant Disbursement Analysis:")
    print("-" * 60)
    
    for grant in grants:
        grant_id, code, title, disbursement_type, tranche_count = grant
        print(f"Grant {grant_id}: {code}")
        print(f"  Title: {title}")
        print(f"  Disbursement Type: '{disbursement_type}'")
        print(f"  Tranches in DB: {tranche_count}")
        
        if disbursement_type == 'tranches' and tranche_count == 0:
            print(f"  ⚠️  ISSUE: Grant marked as 'tranches' but has no tranches!")
        elif disbursement_type != 'tranches' and tranche_count > 0:
            print(f"  ⚠️  ISSUE: Grant has tranches but disbursement type is '{disbursement_type}'!")
        else:
            print(f"  ✅ OK: Configuration matches")
        print()
    
    # Show specific tranche details
    cursor.execute("""
        SELECT g.grant_code, g.disbursement_type, t.id, t.amount, t.expected_date, t.status
        FROM tranches t
        JOIN grants g ON t.grant_id = g.id
        ORDER BY g.grant_code, t.expected_date
    """)
    
    tranches = cursor.fetchall()
    
    if tranches:
        print("💰 Tranche Details:")
        print("-" * 60)
        for tranche in tranches:
            grant_code, disbursement_type, tranche_id, amount, expected_date, status = tranche
            print(f"{grant_code} (type: {disbursement_type})")
            print(f"  Tranche {tranche_id}: ${amount:,.2f} (Due: {expected_date}, Status: {status})")
    else:
        print("❌ No tranches found in database!")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
