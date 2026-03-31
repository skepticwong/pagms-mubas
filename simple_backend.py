#!/usr/bin/env python3
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from flask import Flask, jsonify, session, request
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'test-secret-key'
CORS(app, supports_credentials=True)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'pagms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initialize db
from models import db
db.init_app(app)

@app.before_first_request
def setup():
    with app.app_context():
        db.create_all()

@app.route('/api/me')
def check_auth():
    user_id = session.get('user_id')
    if user_id:
        return jsonify({'user_id': user_id, 'authenticated': True})
    return jsonify({'authenticated': False})

@app.route('/api/grants')
def get_grants():
    """Simple grants endpoint for testing"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from models import User, Grant
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Simple query based on role
        if user.role == 'RSU':
            grants = Grant.query.all()
        elif user.role == 'PI':
            grants = Grant.query.filter_by(pi_id=user_id).all()
        else:
            grants = []
        
        result = []
        for grant in grants:
            result.append({
                'id': grant.id,
                'title': grant.title,
                'funder': grant.funder,
                'total_budget': grant.total_budget,
                'status': grant.status
            })
        
        return jsonify({'grants': result})
        
    except Exception as e:
        print(f"Error in grants endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Simple login for testing"""
    data = request.get_json() if hasattr(request, 'get_json') else {}
    email = data.get('email')
    password = data.get('password')
    
    # Simple test login - accept any credentials for testing
    from models import User
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create test user if not exists
        user = User(name="Test User", email=email, role="PI")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    
    session['user_id'] = user.id
    return jsonify({'success': True, 'user': {'id': user.id, 'name': user.name, 'role': user.role}})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database created/initialized")
        
        # Create test user if none exists
        from models import User
        if User.query.count() == 0:
            test_user = User(name="Test PI", email="pi@test.com", role="PI")
            test_user.set_password("test123")
            db.session.add(test_user)
            db.session.commit()
            print("Test user created")
    
    print("Starting simple backend on http://localhost:5000")
    app.run(debug=True, port=5000)
