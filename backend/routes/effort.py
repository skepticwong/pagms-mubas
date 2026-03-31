# backend/routes/effort.py
from flask import Blueprint, request, jsonify, session
from models import db, User, Grant, GrantTeam, EffortCertification
from services.effort_service import EffortService
from datetime import datetime
import calendar

effort_bp = Blueprint('effort', __name__)

def _get_previous_month_period():
    today = datetime.now()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1

def _resolve_period_from_query():
    """
    Resolve effort period from query params.
    Defaults to previous month if month/year not provided.
    """
    month_q = request.args.get('month')
    year_q = request.args.get('year')

    if month_q is None and year_q is None:
        return _get_previous_month_period(), None

    try:
        month = int(month_q)
        year = int(year_q)
    except (TypeError, ValueError):
        return None, "month and year must be valid integers"

    if month < 1 or month > 12:
        return None, "month must be between 1 and 12"
    if year < 2000 or year > 2100:
        return None, "year must be between 2000 and 2100"

    return (year, month), None

@effort_bp.route('/effort/status/<int:grant_id>', methods=['GET'])
def get_effort_status(grant_id):
    """
    Check if the grant is locked for spending due to missing certification.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    period, period_err = _resolve_period_from_query()
    if period_err:
        return jsonify({'error': period_err}), 400
    year, month = period

    is_locked, message, severity = EffortService.get_period_compliance(grant_id, year, month)
    
    return jsonify({
        'is_locked': is_locked,
        'message': message,
        'severity': severity,
        'period': {'month': month, 'year': year, 'month_name': calendar.month_name[month]}
    }), 200

@effort_bp.route('/effort/pending/<int:grant_id>', methods=['GET'])
def get_pending_effort(grant_id):
    """
    Fetch pending effort for PI and Team members.
    PI see everyone; Team see only themselves.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    grant = Grant.query.get(grant_id)
    if not grant:
        return jsonify({'error': 'Grant not found'}), 404

    period, period_err = _resolve_period_from_query()
    if period_err:
        return jsonify({'error': period_err}), 400
    year, month = period

    results = []
    
    # Visibility Logic
    is_pi = (user.role == 'PI' and grant.pi_id == user_id)
    is_co_pi = False
    
    # Check for Co-PI role in GrantTeam
    membership = GrantTeam.query.filter_by(grant_id=grant_id, user_id=user_id, status='active').first()
    if membership and membership.role == 'Co-PI':
        is_co_pi = True
        
    if is_pi or is_co_pi:
        # 1. PI's / Co-PI's own effort
        owner_stats = EffortService.get_uncertified_effort(user_id, grant_id, year, month)
        owner_stats['user_name'] = user.name
        owner_stats['role'] = membership.role if membership else 'PI'
        owner_stats['is_self'] = True
        owner_stats['user_id'] = user_id
        results.append(owner_stats)

        # 2. Other Team members
        team_members = GrantTeam.query.filter_by(grant_id=grant_id, status='active').all()
        for member in team_members:
            if member.user_id == user_id:
                continue # Already added as 'owner_stats'
            stats = EffortService.get_uncertified_effort(member.user_id, grant_id, year, month)
            stats['user_name'] = member.user.name
            stats['role'] = member.role
            stats['is_self'] = False
            stats['user_id'] = member.user_id
            results.append(stats)
            
        # 3. Add primary PI to the list if the current user is a Co-PI
        if is_co_pi:
            pi_user = User.query.get(grant.pi_id)
            if pi_user:
                pi_stats = EffortService.get_uncertified_effort(pi_user.id, grant_id, year, month)
                pi_stats['user_name'] = pi_user.name
                pi_stats['role'] = 'PI'
                pi_stats['is_self'] = False
                pi_stats['user_id'] = pi_user.id
                results.append(pi_stats)
    else:
        # Regular team member: see only self
        if not membership:
            return jsonify({'error': 'Not authorized for this grant'}), 403
        
        stats = EffortService.get_uncertified_effort(user_id, grant_id, year, month)
        stats['user_name'] = user.name
        stats['role'] = membership.role
        stats['is_self'] = True
        stats['user_id'] = user_id
        results.append(stats)

    return jsonify({
        'period': {'month': month, 'year': year, 'month_name': calendar.month_name[month]},
        'effort_records': results
    }), 200

@effort_bp.route('/effort/certify', methods=['POST'])
def certify_effort():
    """
    Submit a certification for a user/grant/period.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    grant_id = data.get('grant_id')
    year = data.get('year')
    month = data.get('month')
    percentage = data.get('percentage')
    signature = data.get('signature')
    target_user_id = data.get('user_id', user_id) # PI can certify for team? No, usually everyone certifies themselves, or PI certifies FOR the grant.
    # In "Team First" rule, PI certifies their own but only AFTER team is done.
    
    if not all([grant_id, year, month, percentage, signature]):
        return jsonify({'error': 'Missing fields'}), 400

    grant = Grant.query.get(grant_id)
    user = User.query.get(user_id)
    
    is_pi = (user.role == 'PI' and grant.pi_id == user_id and int(target_user_id) == user_id)
    
    try:
        cert = EffortService.certify_effort(
            user_id=target_user_id,
            grant_id=grant_id,
            year=year,
            month=month,
            percentage=float(percentage),
            signature=signature,
            ip=request.remote_addr,
            is_pi=is_pi
        )
        return jsonify({'message': 'Effort certified successfully', 'certification': cert.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to certify effort', 'details': str(e)}), 500

@effort_bp.route('/effort/override', methods=['POST'])
def apply_override():
    """
    RSU-only endpoint to apply override.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if user.role != 'RSU':
        return jsonify({'error': 'Only RSU can apply overrides'}), 403
    
    data = request.get_json()
    grant_id = data.get('grant_id')
    year = data.get('year')
    month = data.get('month')
    justification = data.get('justification')
    
    if not all([grant_id, year, month, justification]):
        return jsonify({'error': 'Missing fields'}), 400

    try:
        cert = EffortService.apply_override(grant_id, year, month, justification)
        return jsonify({'message': 'RSU Override applied successfully', 'certification': cert.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to apply override', 'details': str(e)}), 500

@effort_bp.route('/effort/locked-grants', methods=['GET'])
def get_locked_grants():
    """
    RSU-only endpoint: return all grants that are currently spending-locked
    due to missing effort certification.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    from models import Grant
    import calendar as cal

    today = datetime.now()
    if today.month == 1:
        prev_month, prev_year = 12, today.year - 1
    else:
        prev_month, prev_year = today.month - 1, today.year

    all_grants = Grant.query.all()
    locked = []

    for grant in all_grants:
        is_locked, message, severity = EffortService.check_spending_lock(grant.id)
        if is_locked:
            locked.append({
                'grant_id': grant.id,
                'grant_code': grant.grant_code,
                'title': grant.title,
                'pi_id': grant.pi_id,
                'message': message,
                'prev_month': prev_month,
                'prev_year': prev_year,
                'month_name': cal.month_name[prev_month]
            })

    return jsonify({'locked_grants': locked, 'period': {'month': prev_month, 'year': prev_year}}), 200

