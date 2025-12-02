# backend/routes/auth.py
from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint
    Expects: { "email": "...", "password": "..." }
    Returns: user object or 401
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        
        user = AuthService.login(email, password)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Store user ID in session (secure cookie)
        session['user_id'] = user.id
        
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear session"""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expects: { "name": "...", "email": "...", "password": "...", "role": "...", "pay_rate": ... }
    Returns: user object or error
    """
    try:
        data = request.get_json() or {}
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'Team')  # Default to Team if not specified
        pay_rate = data.get('pay_rate')  # Optional
        
        user = AuthService.register(name, email, password, role, pay_rate)
        
        # Automatically log in the user after registration
        session['user_id'] = user.id
        
        return jsonify(user.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get user', 'details': str(e)}), 500