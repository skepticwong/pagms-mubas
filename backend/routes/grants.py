# backend/routes/grants.py
from flask import Blueprint, request, jsonify
from services.grant_service import GrantService
from datetime import datetime

grants_bp = Blueprint('grants', __name__)

@grants_bp.route('/grants', methods=['POST'])
def create_grant():
    """
    Create a new grant
    Expects: { "title": "...", "funder": "...", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "total_budget": ... }
    Returns: grant object or error
    """
    try:
        data = request.get_json() or {}
        
        # Parse dates
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        # Call service
        grant = GrantService.create_grant(
            title=data.get('title'),
            funder=data.get('funder'),
            start_date=start_date,
            end_date=end_date,
            total_budget=float(data.get('total_budget', 0)),
            pi_id=data.get('pi_id')  # Optional, will use first PI if not provided
        )
        return jsonify(grant.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500

@grants_bp.route('/grants', methods=['GET'])
def get_grants():
    """
    Get all grants
    Returns: list of grant objects
    """
    try:
        grants = GrantService.get_all_grants()
        return jsonify([g.to_dict() for g in grants]), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch grants', 'details': str(e)}), 500