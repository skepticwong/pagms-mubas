# backend/routes/misc.py
from flask import Blueprint, jsonify, session, request
from models import AuditLog, User, Task, GrantTeam, Notification, DeliverableSubmission, Grant, Milestone, EffortCertification, db
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


# ─── Team Module: New Endpoints ──────────────────────────────────────────────

@misc_bp.route('/me/deadlines', methods=['GET'])
def get_my_deadlines():
    """Unified personal deadline aggregator for the Team Member dashboard."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from services.deadline_service import DeadlineService
        deadlines = DeadlineService.get_user_deadlines(user_id)
        return jsonify({'deadlines': deadlines}), 200
    except Exception as e:
        print(f"Error fetching deadlines: {str(e)}")
        return jsonify({'error': 'Failed to fetch deadlines', 'details': str(e)}), 500


@misc_bp.route('/me/impact', methods=['GET'])
def get_my_impact():
    """Personal contribution & impact stats for the Impact Report page."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Total tasks
        all_tasks = Task.query.filter_by(assigned_to=user_id).all()
        completed_tasks = [t for t in all_tasks if t.status.upper() == 'COMPLETED']

        # Total deliverable submissions
        submissions = DeliverableSubmission.query.filter_by(user_id=user_id).all()
        approved_submissions = [s for s in submissions if s.verification_status == 'approved']
        total_hours = sum(s.hours_worked or 0 for s in approved_submissions)

        # Milestone contribution: milestones that have at least one completed task assigned to this user
        milestones_contributed = set()
        for task in completed_tasks:
            if task.milestone_id:
                milestones_contributed.add(task.milestone_id)

        contributed_milestones = []
        for mid in milestones_contributed:
            milestone = Milestone.query.get(mid)
            if milestone:
                contributed_milestones.append({
                    'id': milestone.id,
                    'title': milestone.title,
                    'status': milestone.status,
                    'progress': milestone.progress_percentage,
                    'grant': milestone.grant.title if milestone.grant else 'N/A'
                })

        # Effort certifications
        certifications = EffortCertification.query.filter_by(user_id=user_id, status='VERIFIED').all()

        # Grant memberships for context
        memberships = GrantTeam.query.filter_by(user_id=user_id, status='active').all()
        active_grants = len(memberships)

        return jsonify({
            'stats': {
                'total_tasks': len(all_tasks),
                'completed_tasks': len(completed_tasks),
                'completion_rate': round((len(completed_tasks) / len(all_tasks) * 100) if all_tasks else 0, 1),
                'total_deliverables': len(submissions),
                'approved_deliverables': len(approved_submissions),
                'total_verified_hours': round(total_hours, 1),
                'milestones_contributed': len(milestones_contributed),
                'effort_certifications_signed': len(certifications),
                'active_grants': active_grants
            },
            'contributed_milestones': contributed_milestones
        }), 200
    except Exception as e:
        print(f"Error fetching impact: {str(e)}")
        return jsonify({'error': 'Failed to fetch impact data', 'details': str(e)}), 500


@misc_bp.route('/tasks/<int:task_id>/progress-note', methods=['POST'])
def log_progress_note(task_id):
    """Log a progress note on a task — silently notifies the PI."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    note = data.get('note', '').strip()
    if not note:
        return jsonify({'error': 'Note text is required'}), 400

    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        updater = User.query.get(user_id)
        if not updater:
            return jsonify({'error': 'User not found'}), 404

        # Write audit log entry
        log = AuditLog(
            user_id=user_id,
            action='PROGRESS_NOTE',
            resource_type='task',
            resource_id=task_id,
            details=note,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)

        # Send silent notification to PI
        if task.grant and task.grant.pi_id:
            notif = Notification(
                user_id=task.grant.pi_id,
                type='TASK_PROGRESS_UPDATE',
                message=f"📝 {updater.name} updated Task #{task_id} \"{task.title}\": {note}",
                created_at=datetime.utcnow()
            )
            db.session.add(notif)

        db.session.commit()

        return jsonify({'message': 'Progress note logged and PI notified.'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error logging progress note: {str(e)}")
        return jsonify({'error': 'Failed to log progress note', 'details': str(e)}), 500


@misc_bp.route('/me/my-inventory', methods=['GET'])
def get_my_inventory():
    """Assets currently in the logged-in user's custody."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        from models import Asset
        assets = Asset.query.filter_by(custodian_user_id=user_id).filter(
            Asset.status.in_(['ACTIVE', 'LENDED'])
        ).all()
        return jsonify({'assets': [a.to_dict() for a in assets]}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch inventory', 'details': str(e)}), 500