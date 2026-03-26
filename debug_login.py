#!/usr/bin/env python3
import os
import sys

print("=== PAGMS Login Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
print(f"Backend path: {backend_path}")
sys.path.insert(0, backend_path)

try:
    print("\nImporting app...")
    from app import create_app
    print("✅ App imported successfully")
    
    print("Creating app...")
    app = create_app()
    print("✅ App created successfully")
    
    with app.app_context():
        print("Importing models...")
        from models import db, User
        print("✅ Models imported")
        
        print("Creating tables...")
        db.create_all()
        print("✅ Tables created")
        
        print("Checking users...")
        users = User.query.all()
        print(f"Found {len(users)} users")
        
        if len(users) == 0:
            print("Creating demo users...")
            from services.auth_service import AuthService
            
            demo_users = [
                ('Principal Investigator', 'pi@mubas.ac.mw', 'mubas123', 'PI'),
                ('Team Member', 'team@mubas.ac.mw', 'mubas123', 'Team'),
                ('Finance Officer', 'finance@mubas.ac.mw', 'mubas123', 'Finance'),
                ('RSU Officer', 'rsu@mubas.ac.mw', 'mubas123', 'RSU')
            ]
            
            for name, email, password, role in demo_users:
                try:
                    user = AuthService.create_user(name, email, role, password)
                    print(f"✅ Created {email}")
                except Exception as e:
                    print(f"❌ Error creating {email}: {e}")
        
        print("\nTesting login...")
        from services.auth_service import AuthService
        test_user = AuthService.login('pi@mubas.ac.mw', 'mubas123')
        if test_user:
            print(f"✅ Login successful: {test_user.name} ({test_user.role})")
        else:
            print("❌ Login failed")
            
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")
