# backend/app.py
import os
from flask import Flask
from flask_cors import CORS

# ✅ IMPORT db from models — NOT creating a new one
from models import db
from routes.auth import auth_bp
from routes.grants import grants_bp
from routes.misc import misc_bp
from routes.tasks import tasks_bp
from routes.users import users_bp
from routes.reports import reports_bp
from routes.expenses import expenses_bp
from routes.finance import finance_bp
from routes.documents import documents_bp
from routes.rules import rules_bp
from flask import send_from_directory

def create_app():
    app = Flask(__name__)
    app.secret_key = 'pagms-mubas-secret-2025-change-in-production'
    
    # Critical for localhost (HTTP) development
    # ✅ Critical for localhost (HTTP) development
    app.config.update(
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False  # ← Must be False on http://localhost
    )
    
    CORS(app, 
         origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
         supports_credentials=True, 
         intercept_exceptions=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'pagms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Automatic Column Migration for ExpenseClaim
    def check_and_patch_db():
        with app.app_context():
            import sqlite3
            db_path = os.path.join(app.instance_path, 'pagms.db')
            if not os.path.exists(db_path):
                return
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(expense_claims)")
            columns = [col[1] for col in cursor.fetchall()]
            
            needed = [
                ("expense_date", "DATE"),
                ("description", "TEXT"),
                ("receipt_filename", "VARCHAR(200)"),
                ("payment_method", "VARCHAR(50)")
            ]
            
            patched = False
            for col_name, col_type in needed:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE expense_claims ADD COLUMN {col_name} {col_type}")
                        patched = True
                    except Exception as e:
                        print(f"Error migrating {col_name}: {e}")
            
            # --- Migrating rules & profiles & grants ---
            updates = [
                ("rule_profiles", "created_at", "DATETIME"),
                ("rule_profiles", "funder_id", "VARCHAR(100)"),
                ("rules", "priority_level", "INTEGER"),
                ("rules", "guidance_text", "TEXT"),
                ("rules", "is_active", "BOOLEAN"),
                ("rules", "created_at", "DATETIME"),
                ("grants", "rule_profile_id", "INTEGER"),
                ("grants", "rule_snapshot_id", "INTEGER"),
                ("grants", "reporting_template_filename", "VARCHAR(200)"),
                ("rule_profiles", "reporting_template_filename", "VARCHAR(200)")
            ]
            
            for table_name, col_name, col_type in updates:
                try:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    table_info = cursor.fetchall()
                    if table_info: # Table exists
                        cols = [c[1] for c in table_info]
                        if col_name not in cols:
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                            patched = True
                except Exception as e:
                    print(f"Error migrating {table_name}.{col_name}: {e}")

            # --- Fix rule_profile_rules association table names ---
            try:
                cursor.execute("PRAGMA table_info(rule_profile_rules)")
                table_info = cursor.fetchall()
                if table_info:
                    rpr_cols = [c[1] for c in table_info]
                    if 'profile_id' not in rpr_cols:
                        cursor.execute("DROP TABLE rule_profile_rules")
                        patched = True
            except Exception as e:
                pass

            if patched:
                conn.commit()
            conn.close()

    try:
        check_and_patch_db()
    except Exception as e:
        print(f"Migration error: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(grants_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')
    app.register_blueprint(tasks_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(expenses_bp, url_prefix='/api')
    app.register_blueprint(finance_bp, url_prefix='/api')
    app.register_blueprint(documents_bp, url_prefix='/api')
    app.register_blueprint(rules_bp, url_prefix='/api')

    @app.route('/api/uploads/<path:filename>')
    def serve_uploads(filename):
        uploads_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(uploads_dir, filename)

    return app

app = create_app()

with app.app_context():
    from models import User, Grant
    db.create_all()
    
    if User.query.count() == 0:
        from services.auth_service import AuthService
        AuthService.create_user('Dr. PI', 'pi@mubas.ac.mw', 'PI', 'mubas123')
        AuthService.create_user('Team Member', 'team@mubas.ac.mw', 'Team', 'mubas123')
        AuthService.create_user('Finance Officer', 'finance@mubas.ac.mw', 'Finance', 'mubas123')
        AuthService.create_user('RSU Admin', 'rsu@mubas.ac.mw', 'RSU', 'mubas123')

if __name__ == '__main__':
    # Using 0.0.0.0 to resolve localhost vs 127.0.0.1 issues
    app.run(debug=True, host='0.0.0.0', port=5000)