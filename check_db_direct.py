import sqlite3
import os

db_path = os.path.join('backend', 'instance', 'pagms.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if grants table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grants'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("🔍 CHECKING GRANTS IN DATABASE")
        print("=" * 50)
        
        # Get all grants
        cursor.execute("SELECT id, grant_code, title, funder, total_budget, status, disbursement_type, created_at FROM grants ORDER BY id")
        grants = cursor.fetchall()
        
        print(f"\n📊 Total Grants: {len(grants)}")
        print("=" * 50)
        
        if not grants:
            print("❌ No grants found in database.")
        else:
            for i, grant in enumerate(grants, 1):
                print(f"\n🎯 Grant #{i}")
                print(f"   ID: {grant[0]}")
                print(f"   Code: {grant[1]}")
                print(f"   Title: {grant[2]}")
                print(f"   Funder: {grant[3]}")
                print(f"   Budget: ${grant[4]:,.2f}" if grant[4] else "   Budget: N/A")
                print(f"   Status: {grant[5]}")
                print(f"   Disbursement: {grant[6]}")
                print(f"   Created: {grant[7]}")
                print("-" * 50)
        
        # Check tranches
        cursor.execute("SELECT COUNT(*) FROM tranches")
        tranche_count = cursor.fetchone()[0]
        print(f"\n💰 Total Tranches: {tranche_count}")
        
        if tranche_count > 0:
            cursor.execute("""
                SELECT g.grant_code, t.id, t.amount, t.expected_date, t.status 
                FROM tranches t 
                JOIN grants g ON t.grant_id = g.id 
                ORDER BY g.grant_code, t.expected_date
            """)
            tranches = cursor.fetchall()
            
            print("\n📋 Tranche Details:")
            for tranche in tranches:
                print(f"   {tranche[0]} - Tranche {tranche[1]}: ${tranche[2]:,.2f} (Due: {tranche[3]}, Status: {tranche[4]})")
        
        # Check milestones
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestone_count = cursor.fetchone()[0]
        print(f"\n🎯 Total Milestones: {milestone_count}")
        
        # Check budget categories
        cursor.execute("SELECT COUNT(*) FROM budget_categories")
        category_count = cursor.fetchone()[0]
        print(f"📁 Total Budget Categories: {category_count}")
        
    else:
        print("❌ Grants table not found in database.")
        print("Available tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"   - {table[0]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Database path: {db_path}")
    print(f"File exists: {os.path.exists(db_path)}")
