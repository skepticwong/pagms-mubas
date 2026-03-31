# backend/routes/grants.py
from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
from models import db, Grant, BudgetCategory, User, AuditLog, Milestone, Tranche

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
    """Get all grants for current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from services.grant_service_simple import GrantServiceSimple
        grants = GrantServiceSimple.get_grants_for_user(user_id)
        return jsonify({'grants': grants}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch grants', 'details': str(e)}), 500

@grants_bp.route('/pi-dashboard/action-items', methods=['GET'])
def get_pi_action_items():
    """Get summarized action items for the PI dashboard."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from services.grant_service import GrantService
        actions = GrantService.get_pi_action_items(user_id)
        return jsonify(actions), 200
    except Exception as e:
        print(f"Error fetching PI action items: {str(e)}")
        return jsonify({'error': 'Failed to fetch action items', 'details': str(e)}), 500

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
    if not user or user.role not in ['PI', 'RSU']:
        return jsonify({'error': 'Only PIs and RSU Admins can view budget data'}), 403

    try:
        from services.grant_service_simple import GrantServiceSimple
        # The get_grants_for_user method already filters by PI and includes necessary details
        grants_data = GrantServiceSimple.get_grants_for_user(user_id)
        
        # Calculate summary statistics for the overview cards
        total_allocated = sum(g['total_budget'] for g in grants_data)
        total_spent = sum(g['total_budget'] * g['spent_percent'] / 100 for g in grants_data)
        
        avg_burn = 0
        if total_allocated > 0:
            avg_burn = round((total_spent / total_allocated) * 100, 1)

        # Count active funders (unique funders)
        active_funders = len(set(g['funder'] for g in grants_data))

        # Count ethics-protected projects using the new ethics_required flag
        ethics_protected_projects = sum(1 for g in grants_data if g.get('ethics_required'))


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
        budget_authority = data.get('budget_authority', False)

        new_team_member_entry = GrantTeamService.add_team_member_to_grant(
            grant_id, member_user_id, role, user_id, budget_authority
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

@grants_bp.route('/grants/<int:grant_id>/co-pis', methods=['GET'])
def get_co_pis(grant_id):
    """
    Get all active Co-PIs for a specific grant.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from models import GrantTeam, User
        co_pis = GrantTeam.query.filter_by(
            grant_id=grant_id, 
            role='Co-PI', 
            status='active'
        ).all()
        
        results = []
        for cp in co_pis:
            u = User.query.get(cp.user_id)
            if u:
                data = cp.to_dict()
                data['name'] = u.name
                data['email'] = u.email
                results.append(data)
        
        return jsonify(grant.to_dict()), 200
    except Exception as e:
        print(f"Error fetching grant: {str(e)}")
        return jsonify({'error': 'Failed to fetch grant'}), 500

@grants_bp.route('/grants/<int:grant_id>/ethics-reinstatement', methods=['PUT'])
def ethics_reinstatement(grant_id):
    """
    PI uploads new ethics certificate after expiry/suspension.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    grant = Grant.query.get(grant_id)
    if not grant:
        return jsonify({'error': 'Grant not found'}), 404
        
    if grant.pi_id != user_id:
        return jsonify({'error': 'Only the PI can submit reinstatement requests'}), 403

    try:
        from services.grant_service import GrantService
        # Update ethics fields
        grant.ethics_approval_number = request.form.get('ethics_approval_number')
        grant.ethics_expiry_date = datetime.strptime(request.form.get('ethics_expiry_date'), '%Y-%m-%d').date()
        grant.ethics_status = 'PENDING_ETHICS'
        
        # Handle file upload
        certificate_file = request.files.get('ethics_certificate')
        if certificate_file:
            grant.ethics_certificate_filename = GrantService._save_file(certificate_file, 'ethics')
            
        db.session.commit()
        
        # Log Audit Trail
        from services.audit_service import AuditService
        AuditService.log_action(
            user_id=user_id,
            action='ETHICS_REINSTATEMENT_REQUESTED',
            entity_type='GRANT',
            entity_id=grant_id,
            details={'approval_number': grant.ethics_approval_number}
        )
        
        return jsonify({
            'message': 'Reinstatement request submitted. Awaiting RSU verification.',
            'grant': grant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Reinstatement error: {str(e)}")
        return jsonify({'error': f'Failed to submit reinstatement: {str(e)}'}), 500

# ─── RSU Ethics Management ──────────────────────────────────────────────────

@grants_bp.route('/rsu/ethics-queue', methods=['GET'])
def get_ethics_queue():
    """
    Get all grants pending ethics verification (RSU only).
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Unauthorized'}), 403
        
    from services.rsu_service import RSUService
    pending_grants = RSUService.get_pending_ethics_grants()
    
    return jsonify({
        'grants': [g.to_dict() for g in pending_grants]
    }), 200

@grants_bp.route('/rsu/grants/<int:grant_id>/verify-ethics', methods=['PUT'])
def verify_ethics(grant_id):
    """
    Verify the ethics certificate (RSU only).
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json() or {}
    notes = data.get('notes')
    approval_number = data.get('approval_number')
    expiry_date = data.get('expiry_date')
    
    from services.rsu_service import RSUService
    try:
        grant = RSUService.verify_ethics_certificate(grant_id, user_id, approval_number, expiry_date, notes)
        return jsonify({
            'message': 'Ethics certificate verified successfully',
            'grant': grant.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grants_bp.route('/rsu/grants/<int:grant_id>/reject-ethics', methods=['PUT'])
def reject_ethics(grant_id):
    """
    Reject the ethics certificate (RSU only).
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json() or {}
    reason = data.get('reason')
    if not reason:
        return jsonify({'error': 'Reason for rejection is required'}), 400
        
    from services.rsu_service import RSUService
    try:
        grant = RSUService.reject_ethics_certificate(grant_id, user_id, reason)
        return jsonify({
            'message': 'Ethics certificate rejected',
            'grant': grant.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@grants_bp.route('/grants/<int:grant_id>/tranche-status', methods=['GET'])
def get_tranche_status(grant_id):
    """
    Check if a specific tranche can be released based on milestones and financial reports.
    Expects ?tranche_number=...
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        tranche_number = request.args.get('tranche_number', type=int)
        if not tranche_number:
            return jsonify({'error': 'tranche_number is required'}), 400

        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404

        can_release = grant.can_release_tranche(tranche_number)
        return jsonify({
            'grant_id': grant.id,
            'tranche_number': tranche_number,
            'can_release': can_release
        }), 200
    except Exception as e:
        print(f"Error checking tranche status: {str(e)}")
        return jsonify({'error': 'Failed to check tranche status', 'details': str(e)}), 500

@grants_bp.route('/grants/<int:grant_id>/tranches', methods=['GET'])
def get_grant_tranches(grant_id):
    """
    Get all tranches for a specific grant.
    Returns: tranche data with amounts, dates, status
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Get tranches for this grant, ordered by expected date
        tranches = Tranche.query.filter_by(grant_id=grant_id).order_by(Tranche.expected_date.asc()).all()
        
        # Add tranche_number for UI (1-based index)
        results = []
        for i, tranche in enumerate(tranches):
            d = tranche.to_dict()
            d['tranche_number'] = i + 1  # Add 1-based numbering
            results.append(d)
        
        return jsonify(results), 200
    except Exception as e:
        print(f"Error fetching tranches: {str(e)}")
        return jsonify({'error': 'Failed to fetch tranches', 'details': str(e)}), 500

# --- Milestone Management Routes ---

@grants_bp.route('/grants/<int:grant_id>/milestones', methods=['GET'])
def get_milestones(grant_id):
    """Fetch all milestones for a grant."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    milestones = Milestone.query.filter_by(grant_id=grant_id).order_by(Milestone.due_date.asc()).all()
    # Add sequence number for the UI if not present in DB
    results = []
    for i, m in enumerate(milestones):
        d = m.to_dict()
        d['sequence'] = i + 1
        results.append(d)
    return jsonify(results), 200

@grants_bp.route('/milestones', methods=['POST'])
def create_milestone():
    """Create a new milestone."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    try:
        milestone = Milestone(
            grant_id=data['grant_id'],
            title=data['title'],
            description=data.get('description'),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
            reporting_period=data.get('reporting_period'),
            triggers_tranche=data.get('triggers_tranche')
        )
        db.session.add(milestone)
        db.session.commit()
        return jsonify(milestone.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@grants_bp.route('/milestones/<int:milestone_id>', methods=['PUT'])
def update_milestone(milestone_id):
    """Update an existing milestone."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    milestone = Milestone.query.get(milestone_id)
    if not milestone:
        return jsonify({'error': 'Milestone not found'}), 404
    
    data = request.get_json()
    try:
        milestone.title = data.get('title', milestone.title)
        milestone.description = data.get('description', milestone.description)
        if 'due_date' in data:
            milestone.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        milestone.reporting_period = data.get('reporting_period', milestone.reporting_period)
        milestone.triggers_tranche = data.get('triggers_tranche', milestone.triggers_tranche)
        
        db.session.commit()
        return jsonify(milestone.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@grants_bp.route('/milestones/<int:milestone_id>', methods=['DELETE'])
def delete_milestone(milestone_id):
    """Delete a milestone."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    milestone = Milestone.query.get(milestone_id)
    if not milestone:
        return jsonify({'error': 'Milestone not found'}), 404
    
    try:
        db.session.delete(milestone)
        db.session.commit()
        return jsonify({'message': 'Milestone deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@grants_bp.route('/milestones/<int:milestone_id>/reopen', methods=['PUT'])
def reopen_milestone(milestone_id):
    """Reopen a completed milestone."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from services.milestone_service import MilestoneService
        milestone = MilestoneService.reopen_milestone(milestone_id, user_id)
        return jsonify(milestone.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reopen milestone', 'details': str(e)}), 500

@grants_bp.route('/grants/<int:grant_id>/milestones/reorder', methods=['POST'])
def reorder_milestones(grant_id):
    """Placeholder for reordering logic if needed."""
    # For now, we'll just return success as the frontend expects it.
    # In a real app, we'd update a 'sequence' or 'order' column.
    return jsonify({'message': 'Order updated'}), 200

@grants_bp.route('/grants/<int:grant_id>/health', methods=['GET'])
def get_grant_health(grant_id):
    """
    Get the current compliance health score for a grant.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    from models import ComplianceHealthScore
    health = ComplianceHealthScore.query.filter_by(grant_id=grant_id).first()
    
    if not health:
        # If not initialized, return a default "Perfect" score
        return jsonify({
            'score': 100,
            'risk_level': 'LOW',
            'financial_risk': 0,
            'operational_risk': 0,
            'reporting_risk': 0,
            'last_calculated': datetime.utcnow().isoformat()
        }), 200
        
    return jsonify(health.to_dict()), 200

@grants_bp.route('/grants/<int:grant_id>/financial-intelligence', methods=['GET'])
def get_grant_financial_intelligence(grant_id):
    """
    Get combined burn rate and forecasting indicators for the PI.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    grant = Grant.query.get(grant_id)
    if not grant:
        return jsonify({'error': 'Grant not found'}), 404
        
    # Permission check: Only PI or RSU
    user = User.query.get(user_id)
    if not user or (grant.pi_id != user.id and user.role != 'RSU'):
        return jsonify({'error': 'Access denied'}), 403

    try:
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        
        # 1. Get fundamental burn rate (Time vs Spend)
        burn_metrics = BurnRateService.calculate_burn_rate(grant_id)
        
        # 2. Get forecasting and risk analysis
        health_indicators = BudgetForecastingService.get_financial_health_indicators(grant_id)
        
        # 3. Get projections
        projections = BurnRateService.calculate_projected_completion(grant_id)
        
        return jsonify({
            'burn_rate': burn_metrics,
            'health': health_indicators,
            'projected_completion': projections
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to calculate financial intelligence', 'details': str(e)}), 500