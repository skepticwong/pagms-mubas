#!/usr/bin/env python3
"""
Minimal backend test
"""

import sys
import os

def main():
    print("🔍 Testing backend imports...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Test basic imports
        print("Testing imports...")
        import flask
        print(f"✅ Flask version: {flask.__version__}")
        
        import flask_sqlalchemy
        print(f"✅ Flask-SQLAlchemy imported")
        
        import flask_cors
        print(f"✅ Flask-CORS imported")
        
        import jwt
        print(f"✅ PyJWT imported")
        
        # Test app creation
        print("Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created successfully!")
        
        # Test database setup
        print("Setting up database...")
        from app import setup_database
        setup_database(app)
        print("✅ Database setup complete!")
        
        # Test models
        print("Testing models...")
        with app.app_context():
            from models import User, Grant, BudgetCategory
            print(f"✅ Models imported successfully")
            print(f"Users in database: {User.query.count()}")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
