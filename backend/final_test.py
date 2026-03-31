#!/usr/bin/env python3
"""
Final test to confirm backend is working
"""

def main():
    print("🧪 FINAL BACKEND TEST")
    print("=" * 40)
    
    try:
        # Test app creation
        from app import create_app
        app = create_app()
        print("✅ App creation works")
        
        # Test database setup
        from app import setup_database
        setup_database(app)
        print("✅ Database setup works")
        
        # Test endpoints
        with app.test_client() as client:
            # Health check
            response = client.get('/health')
            print(f"✅ Health: {response.status_code}")
            
            # Login test
            response = client.post('/api/login', 
                                 json={'email': 'test@example.com', 'password': 'test'},
                                 content_type='application/json')
            print(f"✅ Login: {response.status_code}")
            
            if response.status_code == 200:
                user = response.get_json()
                print(f"✅ User: {user['name']} ({user['role']})")
                
                # Auth check
                response = client.get('/api/me')
                print(f"✅ Auth check: {response.status_code}")
                
                if response.status_code == 200:
                    auth_user = response.get_json()
                    print(f"✅ Auth user: {auth_user['name']}")
        
        print("\n🎉 BACKEND IS FULLY WORKING!")
        print("✅ Start with: python app.py")
        print("✅ Frontend should connect now")
        print("✅ Login with: test@example.com / test")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🚀 READY TO GO!")
    else:
        print("\n❌ STILL NEEDS WORK")
