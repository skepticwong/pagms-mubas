from flask import Blueprint, jsonify, session
from flask_cors import CORS
from services.grant_team_service import GrantTeamService
from models import User

users_bp = Blueprint('users', __name__)
CORS(users_bp, origins=["http://localhost:5173"], supports_credentials=True)

@users_bp.route('/users/available', methods=['GET'])
def get_available_users():
    """
    Get a list of users (non-PI, non-RSU) who can be added to grant teams.
    Only accessible by PIs.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        available_users = GrantTeamService.get_available_users_for_grant_team(user_id)
        return jsonify(available_users), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error fetching available users: {str(e)}")
        return jsonify({'error': 'Failed to fetch available users'}), 500