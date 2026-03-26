from functools import wraps
from flask import session, jsonify
from models import User

def token_required(f):
    """Decorator to ensure user is logged in via session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
            
        # Pass user as the first argument
        return f(user, *args, **kwargs)
    return decorated

def rsu_required(f):
    """Decorator to ensure user has RSU role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Case 1: user already passed (likely from token_required)
        if args and isinstance(args[0], User):
            user = args[0]
        else:
            # Case 2: need to fetch from session
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Not authenticated'}), 401
            user = User.query.get(user_id)

        if not user or user.role != 'RSU':
            return jsonify({'error': 'RSU access required'}), 403
            
        return f(*args, **kwargs)
    return decorated
