#!/usr/bin/env python3
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from services.auth_service import AuthService
from models import db, User

def main():
    print("=== PAGMS Login Debug ===")
    
    # Create app
    app = create_app()
    
    with app.app_context():
        # Create tables
        print("Creating database tables...")
        db.create_all()
        
        # Check existing users
        users = User.query.all()
        print(f"Existing users: {len(users)}")
        for user in users:
            print(f"  - {user.name} ({user.email}) - {user.role}")
        
        # Create demo users if needed
        demo_users = [
            ('Principal Investigator', 'pi@mubas.ac.mw', 'mubas123', 'PI'),
            ('Team Member', 'team@mubas.ac.mw', 'mubas123', 'Team'),
            ('Finance Officer', 'finance@mubas.ac.mw', 'mubas123', 'Finance'),
            ('RSU Officer', 'rsu@mubas.ac.mw', 'mubas123', 'RSU')
        ]
        
        print("\nCreating demo users...")
        for name, email, password, role in demo_users:
            try:
                # Check if user exists
                existing = User.query.filter_by(email=email).first()
                if existing:
                    print(f"✅ {email} already exists")
                else:
                    user = AuthService.create_user(name, email, role, password)
                    print(f"✅ Created {email} ({role})")
            except Exception as e:
                print(f"❌ Error with {email}: {e}")
        
        # Test login
        print("\nTesting login...")
        test_user = AuthService.login('pi@mubas.ac.mw', 'mubas123')
        if test_user:
            print(f"✅ Login successful: {test_user.name} ({test_user.role})")
        else:
            print("❌ Login failed")
        
        print("\n=== Backend is ready! ===")
        print("Demo accounts:")
        print("  PI: pi@mubas.ac.mw / mubas123")
        print("  Team: team@mubas.ac.mw / mubas123")
        print("  Finance: finance@mubas.ac.mw / mubas123")
        print("  RSU: rsu@mubas.ac.mw / mubas123")

if __name__ == "__main__":
    main()
