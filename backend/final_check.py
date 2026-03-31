import sys
import os
import datetime

print("--- DIAGNOSTIC START ---")
print(f"Time: {datetime.datetime.now()}")
print(f"CWD: {os.getcwd()}")

try:
    import flask
    print("Flask ok")
    import flask_sqlalchemy
    print("SQLAlchemy ok")
    import models
    print("Models import ok")
    
    from app import create_app
    app = create_app()
    print("App creation ok")
    
    with app.app_context():
        from models import User, Grant
        print(f"Users in DB: {User.query.count()}")
        print(f"Grants in DB: {Grant.query.count()}")
        
    print("--- DIAGNOSTIC SUCCESS ---")
except Exception as e:
    print(f"--- DIAGNOSTIC FAILURE ---")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
