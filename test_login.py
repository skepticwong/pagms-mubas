#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from backend.services.auth_service import AuthService

def test_login():
    app = create_app()
    
    with app.app_context():
        # Test demo accounts
        demo_accounts = [
            ('pi@mubas.ac.mw', 'mubas123'),
            ('team@mubas.ac.mw', 'mubas123'), 
            ('finance@mubas.ac.mw', 'mubas123'),
            ('rsu@mubas.ac.mw', 'mubas123')
        ]
        
        print("Testing demo accounts...")
        for email, password in demo_accounts:
            try:
                user = AuthService.login(email, password)
                if user:
                    print(f"✅ {email} - Login successful (Role: {user.role})")
                else:
                    print(f"❌ {email} - Login failed")
            except Exception as e:
                print(f"❌ {email} - Error: {e}")
        
        # Create demo users if they don't exist
        print("\nCreating demo users...")
        demo_users = [
            ('Principal Investigator', 'pi@mubas.ac.mw', 'mubas123', 'PI'),
            ('Team Member', 'team@mubas.ac.mw', 'mubas123', 'Team'),
            ('Finance Officer', 'finance@mubas.ac.mw', 'mubas123', 'Finance'),
            ('RSU Officer', 'rsu@mubas.ac.mw', 'mubas123', 'RSU')
        ]
        
        for name, email, password, role in demo_users:
            try:
                user = AuthService.create_user(name, email, role, password)
                print(f"✅ Created {email} ({role})")
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"ℹ️ {email} already exists")
                else:
                    print(f"❌ Error creating {email}: {e}")
            except Exception as e:
                print(f"❌ Unexpected error creating {email}: {e}")

if __name__ == "__main__":
    test_login()
