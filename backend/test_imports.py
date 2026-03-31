#!/usr/bin/env python3
print("Testing imports...")

try:
    print("1. Importing Flask...")
    from flask import Flask, jsonify
    print("   ✓ Flask OK")
except Exception as e:
    print(f"   ✗ Flask error: {e}")

try:
    print("2. Importing app...")
    from app import create_app
    print("   ✓ App import OK")
except Exception as e:
    print(f"   ✗ App import error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("3. Creating app...")
    app = create_app()
    print("   ✓ App creation OK")
except Exception as e:
    print(f"   ✗ App creation error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("4. Testing models...")
    from models import db, User, Grant
    print("   ✓ Models import OK")
except Exception as e:
    print(f"   ✗ Models error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("5. Testing services...")
    from services.grant_service import GrantService
    print("   ✓ GrantService import OK")
except Exception as e:
    print(f"   ✗ GrantService error: {e}")
    import traceback
    traceback.print_exc()

print("Import test complete.")
