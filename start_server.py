#!/usr/bin/env python3
"""
Simple backend server startup script
"""

import sys
import os

def main():
    print("[STARTING] PAGMS Backend Server...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    print(f"[DIR] Changed to directory: {os.getcwd()}")
    
    # Add to Python path
    sys.path.insert(0, os.getcwd())
    
    try:
        # Import and create app
        from app import create_app
        app = create_app()
        print("[OK] App created successfully!")
        
        # Setup database
        from app import setup_database
        with app.app_context():
            setup_database(app)
            print("[OK] Database setup complete!")
            
            # Check users
            from models import User
            user_count = User.query.count()
            print(f"[DB] Users in database: {user_count}")
            
            if user_count == 0:
                print("[WARN] No users found - you may need to register first")
            else:
                user = User.query.first()
                print(f"[USER] First user: {user.name} ({user.email})")
        
        print("\n[SERVER] Starting Flask server on http://localhost:5000")
        print("[API] API is ready!")
        print("[HEALTH] Health check: http://localhost:5000/health")
        print("[AUTH] Auth endpoint: http://localhost:5000/api/me")
        print("\n[INFO] Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start server
        app.run(debug=True, port=5000, host='0.0.0.0')
        
    except Exception as e:
        print(f"[ERROR] Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
