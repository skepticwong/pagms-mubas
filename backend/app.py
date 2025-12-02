# backend/app.py
import os
from flask import Flask
from flask_cors import CORS

# ✅ IMPORT db from models — NOT creating a new one
from models import db
from routes.auth import auth_bp
from routes.grants import grants_bp
from routes.misc import misc_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'pagms-mubas-secret-2025-change-in-production'
    
    # Configure CORS to allow requests from frontend
    # intercept_exceptions=True ensures CORS headers are added even on errors
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True, intercept_exceptions=True)
    
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'pagms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ Initialize the SAME db instance with this app
    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(grants_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')

    return app

app = create_app()

# ✅ Now db is bound to the app — safe to use
with app.app_context():
    # Import models (optional, but safe)
    from models import User, Grant
    
    db.create_all()
    
    if User.query.count() == 0:
        from services.auth_service import AuthService
        AuthService.create_user('Dr. PI', 'pi@mubas.ac.mw', 'PI', 'mubas123')
        AuthService.create_user('Team Member', 'team@mubas.ac.mw', 'Team', 'mubas123')
        AuthService.create_user('Finance Officer', 'finance@mubas.ac.mw', 'Finance', 'mubas123')
        AuthService.create_user('RSU Admin', 'rsu@mubas.ac.mw', 'RSU', 'mubas123')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)