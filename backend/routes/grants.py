# backend/routes/grants.py
from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
from models import db, Grant, BudgetCategory, User, AuditLog

grants_bp = Blueprint('grants', __name__)

@grants_bp.route('/grants', methods=['POST'])
def create_grant():
    """
    Create a new grant — only for logged-in PIs.
    Expects multipart/form-data with fields and files.
    """
    # 1. Verify user is authenticated
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'PI':
        return jsonify({'error': 'Only PIs can create grants'}), 403

    try:
        from services.grant_service import GrantService
        
        # 2. Delegate to Service
        # We pass request.form (for text fields) and request.files (for file uploads)
        grant = GrantService.create_grant(request.form, request.files, user_id)

        return jsonify(grant.to_dict()), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Grant creation error: {str(e)}")  # For debugging
        return jsonify({'error': 'Failed to create grant', 'details': str(e)}), 500

@grants_bp.route('/grants/<int:grant_id>/approve', methods=['PUT'])
def approve_grant(grant_id):
    """
    Approve a grant (RSU Only).
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Only RSU Admins can approve grants'}), 403

    try:
        from services.grant_service import GrantService
        grant = GrantService.approve_grant(grant_id, user_id)
        return jsonify({'message': 'Grant approved successfully', 'grant': grant.to_dict()}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        print(f"Error approving grant: {str(e)}")
        return jsonify({'error': 'Failed to approve grant'}), 500

@grants_bp.route('/grants', methods=['GET'])
def list_grants():
    """Get all grants for the current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from services.grant_service import GrantService
        grants = GrantService.get_grants_for_user(user_id)
        return jsonify(grants), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch grants', 'details': str(e)}), 500

@grants_bp.route('/pi-grants-budget', methods=['GET'])
def get_pi_grants_budget():
    """
    Get all grants for the logged-in PI, specifically for the budget control room.
    Includes budget categories and spent percentages.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'PI':
        return jsonify({'error': 'Only PIs can view budget data'}), 403

    try:
        from services.grant_service import GrantService
        # The get_grants_for_user method already filters by PI and includes necessary details
        grants_data = GrantService.get_grants_for_user(user_id)
        
        # Calculate summary statistics for the overview cards
        total_allocated = sum(g['total_budget'] for g in grants_data)
        total_spent = sum(g['total_budget'] * g['spent_percent'] / 100 for g in grants_data)
        
        avg_burn = 0
        if total_allocated > 0:
            avg_burn = round((total_spent / total_allocated) * 100, 1)

        # Count active funders (unique funders)
        active_funders = len(set(g['funder'] for g in grants_data))

        # Count ethics-protected projects (assuming ethical_approval_filename indicates protection)
        ethics_protected_projects = sum(1 for g in grants_data if g.get('ethical_approval_filename'))


        return jsonify({
            'grants': grants_data,
            'summary': {
                'total_allocated': total_allocated,
                'total_spent': total_spent,
                'avg_burn': avg_burn,
                'active_funders': active_funders,
                'ethics_protected_projects': ethics_protected_projects
            }
        }), 200
    except Exception as e:
        print(f"Error fetching PI grants budget: {str(e)}")
        return jsonify({'error': 'Failed to fetch PI grants budget', 'details': str(e)}), 500

# --- Grant Team Management Routes ---
@grants_bp.route('/grants/<int:grant_id>/team', methods=['POST'])
def add_team_member_to_grant(grant_id):
    """
    Add a user as a team member to a specific grant. Only PI of the grant can do this.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from services.grant_team_service import GrantTeamService # Import GrantTeamService
        data = request.get_json()
        member_user_id = data.get('user_id')
        role = data.get('role')

        new_team_member_entry = GrantTeamService.add_team_member_to_grant(
            grant_id, member_user_id, role, user_id
        )
        
        # Determine if it was a prior approval trigger
        result = new_team_member_entry.to_dict()
        message = 'Team member added successfully.'
        if new_team_member_entry.status == 'awaiting_prior_approval':
            message = 'Addition requires prior approval. Request sent to RSU.'
            
        return jsonify({
            'message': message,
            'member': result
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error adding team member to grant: {str(e)}")
        return jsonify({'error': 'Failed to add team member'}), 500

@grants_bp.route('/grants/<int:grant_id>/team', methods=['GET'])
def get_team_members_for_grant(grant_id):
    """
    Get all team members for a specific grant. Accessible by PI of the grant or RSU.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from services.grant_team_service import GrantTeamService
        team_members = GrantTeamService.get_team_members_for_grant(grant_id, user_id)
        return jsonify(team_members), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error fetching team members for grant: {str(e)}")
        return jsonify({'error': 'Failed to fetch team members'}), 500

@grants_bp.route('/grants/<int:grant_id>/team/<int:member_user_id>', methods=['DELETE'])
def remove_team_member_from_grant(grant_id, member_user_id):
    """
    Remove a team member from a specific grant. Only PI of the grant can do this.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from services.grant_team_service import GrantTeamService
        result = GrantTeamService.remove_team_member_from_grant(
            grant_id, member_user_id, user_id
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error removing team member from grant: {str(e)}")
        return jsonify({'error': 'Failed to remove team member'}), 500

@grants_bp.route('/grants/<int:grant_id>/team/preview', methods=['POST'])
def preview_team_change(grant_id):
    """
    Dry run to check compliance impact of adding a team member.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from services.grant_team_service import GrantTeamService
        data = request.get_json()
        member_user_id = data.get('user_id')
        role = data.get('role')

        preview_result = GrantTeamService.preview_add_team_member(
            grant_id, member_user_id, role, user_id
        )
        return jsonify(preview_result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error previewing team change: {str(e)}")
        return jsonify({'error': 'Failed to preview team change'}), 500

@grants_bp.route('/grants/<int:grant_id>/compliance-summary', methods=['GET'])
def get_grant_compliance_summary(grant_id):
    """
    Get a compliance summary for a specific grant.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from services.compliance_service import ComplianceService
        summary = ComplianceService.get_compliance_summary(grant_id)
        return jsonify(summary), 200
    except Exception as e:
        print(f"Error fetching compliance summary: {str(e)}")
        return jsonify({'error': 'Failed to fetch compliance summary'}), 500