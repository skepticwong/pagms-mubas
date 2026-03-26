#!/usr/bin/env python3
import os
import sys

print("=== PAGMS Backend Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    print("\n1. Testing basic imports...")
    import flask
    print("✅ Flask imported")
    
    import flask_cors
    print("✅ Flask-CORS imported")
    
    print("\n2. Testing app creation...")
    from app import create_app
    app = create_app()
    print("✅ App created successfully")
    
    print("\n3. Testing blueprint imports...")
    from routes.auth import auth_bp
    print("✅ Auth blueprint imported")
    
    from routes.rules import rules_bp
    print("✅ Rules blueprint imported")
    
    print("\n4. Testing database...")
    from models import db
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")
    
    print("\n5. All tests passed! Ready to start server.")
    print("Starting server on http://localhost:5000")
    
    app.run(debug=False, host='localhost', port=5000)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
