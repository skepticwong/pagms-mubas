import sqlite3
import os

db_path = os.path.join('backend', 'instance', 'pagms.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🧹 CLEANING DUPLICATE GRANTS")
    print("=" * 50)
    
    # Find the duplicate grants with code "juu767y7y"
    cursor.execute("SELECT id, grant_code, title, status, created_at FROM grants WHERE grant_code = 'juu767y7y' ORDER BY id")
    duplicate_grants = cursor.fetchall()
    
    print(f"\nFound {len(duplicate_grants)} grants with code 'juu767y7y':")
    for grant in duplicate_grants:
        print(f"   ID: {grant[0]} - {grant[2]} ({grant[3]}) - Created: {grant[4]}")
    
    if len(duplicate_grants) <= 1:
        print("\n✅ No duplicates to remove.")
    else:
        # Keep the first one (oldest), remove the rest
        grants_to_remove = duplicate_grants[1:]  # Skip the first one
        grant_ids_to_remove = [g[0] for g in grants_to_remove]
        
        print(f"\n🗑️  Removing {len(grants_to_remove)} duplicate grants:")
        for grant_id in grants_to_remove:
            print(f"   - Grant ID: {grant_id}")
        
        # Confirm before deletion
        confirm = input(f"\n⚠️  Are you sure you want to delete these {len(grants_to_remove)} grants? (yes/no): ")
        
        if confirm.lower() == 'yes':
            # Delete related records first (to maintain referential integrity)
            
            # Delete budget categories
            cursor.execute(f"DELETE FROM budget_categories WHERE grant_id IN ({','.join(['?'] * len(grant_ids_to_remove))})", grant_ids_to_remove)
            deleted_categories = cursor.rowcount
            print(f"   📁 Deleted {deleted_categories} budget categories")
            
            # Delete milestones
            cursor.execute(f"DELETE FROM milestones WHERE grant_id IN ({','.join(['?'] * len(grant_ids_to_remove))})", grant_ids_to_remove)
            deleted_milestones = cursor.rowcount
            print(f"   🎯 Deleted {deleted_milestones} milestones")
            
            # Delete tranches
            cursor.execute(f"DELETE FROM tranches WHERE grant_id IN ({','.join(['?'] * len(grant_ids_to_remove))})", grant_ids_to_remove)
            deleted_tranches = cursor.rowcount
            print(f"   💰 Deleted {deleted_tranches} tranches")
            
            # Delete the grants themselves
            cursor.execute(f"DELETE FROM grants WHERE id IN ({','.join(['?'] * len(grant_ids_to_remove))})", grant_ids_to_remove)
            deleted_grants = cursor.rowcount
            print(f"   🗑️  Deleted {deleted_grants} grants")
            
            # Commit the transaction
            conn.commit()
            print(f"\n✅ Successfully removed {deleted_grants} duplicate grants and all related data!")
        else:
            print("\n❌ Operation cancelled.")
    
    # Show remaining grants
    cursor.execute("SELECT COUNT(*) FROM grants")
    remaining_grants = cursor.fetchone()[0]
    
    cursor.execute("SELECT id, grant_code, title FROM grants WHERE grant_code = 'juu767y7y'")
    remaining_duplicates = cursor.fetchall()
    
    print(f"\n📊 Database Summary:")
    print(f"   Total grants remaining: {remaining_grants}")
    print(f"   Grants with code 'juu767y7y': {len(remaining_duplicates)}")
    
    if remaining_duplicates:
        for grant in remaining_duplicates:
            print(f"      - ID: {grant[0]}: {grant[1]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    if conn:
        conn.rollback()
        conn.close()
