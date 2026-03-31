import sys
import os

print("--- Test Script Loading ---")

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app import create_app, setup_database
    print("--- Imports Successful ---")
except Exception as e:
    print(f"--- Import Error: {e} ---")
    sys.exit(1)

def test_session_persistence():
    print("=== Testing Session Persistence (using Test Client) ===")
    
    try:
        app = create_app()
        print("--- App Created ---")
        
        # Initialize database for the test
        setup_database(app)
        print("--- Database Setup Complete ---")
        
        app.config['TESTING'] = True
        
        # We'll use a test client to handle cookies automatically
        with app.test_client() as client:
            # 1. Try to access /me without login (should be 401)
            print("\n1. Accessing /api/me without login...")
            response = client.get("/api/me")
            print(f"Status: {response.status_code}")
            if response.status_code == 401:
                print("✅ Correct: 401 Unauthorized")
            else:
                print(f"❌ Unexpected: {response.status_code}")

            # 2. Login
            print("\n2. Logging in as pi@mubas.ac.mw...")
            login_data = {
                "email": "pi@mubas.ac.mw",
                "password": "mubas123"
            }
            response = client.post("/api/login", json=login_data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Login successful")
            else:
                print(f"❌ Login failed: {response.get_data(as_text=True)}")
                return

            # 3. Access /me with session (should be 200)
            print("\n3. Accessing /api/me with session...")
            response = client.get("/api/me")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Auth check successful")
                print(f"User Data: {response.get_json()}")
            else:
                print(f"❌ Auth check failed: {response.status_code} - {response.get_data(as_text=True)}")

            # 4. Logout
            print("\n4. Logging out...")
            response = client.post("/api/logout")
            print(f"Status: {response.status_code}")
            
            # 5. Access /me again (should be 401)
            print("\n5. Accessing /api/me after logout...")
            response = client.get("/api/me")
            print(f"Status: {response.status_code}")
            if response.status_code == 401:
                print("✅ Session correctly cleared")
            else:
                print(f"❌ Session NOT cleared: {response.status_code}")
    except Exception as e:
        print(f"--- Runtime Error: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_persistence()
