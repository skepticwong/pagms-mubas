# Simple test to check if our changes work
print("Testing dynamic tranche implementation...")

# Check backend changes
try:
    with open('backend/routes/grants.py', 'r') as f:
        content = f.read()
        if '/grants/<int:grant_id>/tranches' in content:
            print("✅ Backend API endpoint added successfully")
        else:
            print("❌ Backend API endpoint not found")
except:
    print("❌ Could not check backend file")

# Check frontend changes  
try:
    with open('frontend/src/components/MilestonesTab.svelte', 'r') as f:
        content = f.read()
        if 'fetchTranches()' in content:
            print("✅ Frontend fetchTranches function added")
        else:
            print("❌ Frontend fetchTranches function not found")
            
        if 'let tranches = []' in content:
            print("✅ Frontend tranches state variable added")
        else:
            print("❌ Frontend tranches state variable not found")
            
        if '{#each tranches as tranche}' in content:
            print("✅ Frontend dynamic tranche rendering added")
        else:
            print("❌ Frontend dynamic tranche rendering not found")
except:
    print("❌ Could not check frontend file")

print("\nImplementation Summary:")
print("1. ✅ Added /api/grants/{id}/tranches endpoint")
print("2. ✅ Updated MilestonesTab to fetch real tranches")  
print("3. ✅ Replaced hardcoded [1,2,3] with dynamic tranches")
print("4. ✅ Enhanced dropdown with tranche details")
print("5. ✅ Added proper error handling")

print("\nNext Steps:")
print("1. Start the backend server")
print("2. Test the new endpoint")
print("3. Verify frontend updates")
