
import sys
import os

# Add the backend directory to sys.path
backend_dir = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"
sys.path.append(backend_dir)

try:
    from app import create_app
    print("Attempting to create app...")
    app = create_app()
    print("App created successfully.")
    with app.app_context():
        from models import db, Grant
        print(f"Connected to database: {db.engine.url}")
        grant_count = Grant.query.count()
        print(f"Grant count in DB: {grant_count}")
        print("Diagnostic successful.")
except Exception as e:
    print(f"INITIALIZATION FAILED:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
