import sys
import os
print("Python versions:", sys.version)
print("Current directory:", os.getcwd())
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
print("Backend path:", backend_path)
sys.path.insert(0, backend_path)
try:
    from app import app
    from models import db, User
    print("Imports successful!")
    with app.app_context():
        user_count = User.query.count()
        print(f"Database connected! User count: {user_count}")
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
