#!/usr/bin/env python3
"""
Test backend startup and /api/me endpoint
"""

import sys
import os
import requests
import time

def test_backend():
    print("[TEST] Testing backend startup and /api/me endpoint...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Import and create app
        from app import create_app
        app = create_app()
        print("[OK] App created successfully!")
        
        # Setup database
        from app import setup_database
        setup_database(app)
        print("[OK] Database setup complete!")
        
        # Check users
        with app.app_context():
            from models import User
            print(f'Users in database: {User.query.count()}')
            if User.query.count() > 0:
                user = User.query.first()
                print(f'First user: {user.name} ({user.email})')
            else:
                print('No users found in database')
        
        # Start server in background
        print("[START] Starting Flask server...")
        import threading
        
        def run_server():
            app.run(debug=False, port=5000, host='0.0.0.0', use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Test health endpoint
        print("[TEST] Testing health endpoint...")
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            print(f"Health check status: {response.status_code}")
            print(f"Health check response: {response.json()}")
        except Exception as e:
            print(f"[ERROR] Health check failed: {e}")
        
        # Test /api/me endpoint (should return 401 when not authenticated)
        print("[TEST] Testing /api/me endpoint...")
        try:
            response = requests.get('http://localhost:5000/api/me', timeout=5)
            print(f"/api/me status: {response.status_code}")
            print(f"/api/me response: {response.json()}")
        except Exception as e:
            print(f"[ERROR] /api/me test failed: {e}")
        
        print("[OK] Backend test completed!")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_backend()
