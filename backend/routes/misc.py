# backend/routes/misc.py
from flask import Blueprint, jsonify, session
from models import AuditLog, User, db
from datetime import datetime

misc_bp = Blueprint('misc', __name__)

@misc_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns: API status
    """
    return jsonify({'status': 'ok', 'message': 'PAGMS API is running'}), 200


@misc_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """
    Audit logs for the current user.
    - Team Members: only their own actions.
    - PIs: all actions related to their grants (own actions + team member actions on their grants).
    - RSU: all system actions (future enhancement).
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        if user.role == 'Team':
            # Team members see only their own actions
            audit_logs = AuditLog.query.filter_by(user_id=user_id)\
                .order_by(AuditLog.timestamp.desc())\
                .limit(100).all()
        elif user.role == 'PI':
            # PIs see all actions related to their grants
            from models import Grant, Task, GrantTeam
            
            # Get all grants owned by this PI
            pi_grants = Grant.query.filter_by(pi_id=user_id).all()
            grant_ids = [g.id for g in pi_grants]
            
            # Get all tasks for these grants
            tasks = Task.query.filter(Task.grant_id.in_(grant_ids)).all()
            task_ids = [t.id for t in tasks]
            
            # Get all team members assigned to these grants
            team_entries = GrantTeam.query.filter(GrantTeam.grant_id.in_(grant_ids)).all()
            team_member_ids = [entry.user_id for entry in team_entries]
            
            # Fetch audit logs where:
            # 1. User is the PI themselves
            # 2. User is a team member on their grants
            # 3. Resource is a grant owned by the PI
            # 4. Resource is a task for their grants
            audit_logs = AuditLog.query.filter(
                db.or_(
                    AuditLog.user_id == user_id,  # PI's own actions
                    AuditLog.user_id.in_(team_member_ids),  # Team member actions
                    db.and_(AuditLog.resource_type == 'grant', AuditLog.resource_id.in_(grant_ids)),
                    db.and_(AuditLog.resource_type == 'task', AuditLog.resource_id.in_(task_ids)),
                    db.and_(AuditLog.resource_type == 'expense', AuditLog.resource_id.in_(grant_ids))
                )
            ).order_by(AuditLog.timestamp.desc()).limit(200).all()
        elif user.role == 'RSU':
            # RSU sees all system actions
            audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
        else:
            return jsonify({'error': 'Audit logs not available for this role'}), 403

        # Enrich logs with user names
        logs_list = []
        for log in audit_logs:
            log_user = User.query.get(log.user_id)
            logs_list.append({
                'id': log.id,
                'user_id': log.user_id,
                'user_name': log_user.name if log_user else 'Unknown User',
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'details': log.details,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None
            })

        return jsonify({'audit_logs': logs_list}), 200

    except Exception as e:
        print(f"Error fetching audit logs: {str(e)}")
        return jsonify({'error': 'Failed to fetch audit logs', 'details': str(e)}), 500