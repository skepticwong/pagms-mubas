# backend/routes/auth.py
from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint
    Expects: { "email": "...", "password": "..." }
    Returns: user object with JWT token or 401
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
        
        # Generate JWT token for API access
        from middleware.auth import generate_token
        token = generate_token(user.id)
        
        # Return user data with token
        user_data = user.to_dict()
        user_data['token'] = token
        
        print(f"DEBUG: Login successful for {email}. Returning data: {user_data}")
        return jsonify(user_data), 200
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
    from flask import request, current_app, session
    import jwt
    from models import User
    from services.auth_service import AuthService
    
    try:
        # 1. Try JWT token first
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                parts = auth_header.split(" ")
                if len(parts) == 2:
                    token = parts[1]
            except Exception:
                pass
        
        if token:
            try:
                key = current_app.config.get('SECRET_KEY') or getattr(current_app, 'secret_key', None)
                if key:
                    data = jwt.decode(token, key, algorithms=['HS256'])
                    u = User.query.get(data.get('user_id'))
                    if u:
                        return jsonify(u.to_dict()), 200
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass
            except Exception as e:
                print(f"DEBUG: JWT decode error: {str(e)}")

        # 2. Fallback to session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        return jsonify(user.to_dict()), 200

    except Exception as e:
        print(f"CRITICAL: /me error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Authentication server error', 'details': str(e)}), 500
    
    user = AuthService.get_user_by_id(user_id)
    if not user:
        print(f"DEBUG: user_id {user_id} found in session but NOT in database.")
        return jsonify({'error': 'User not found'}), 401
    
    return jsonify(user.to_dict()), 200