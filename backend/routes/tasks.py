from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, date
from sqlalchemy import func
from models import db, Task, Grant, User, AuditLog, DeliverableSubmission, GrantTeam, Asset
import os
from services.task_service import TaskService # Import the TaskService

tasks_bp = Blueprint('tasks', __name__)

# ─── Permission Helpers ────────────────────────────────────────────────────
def is_co_pi(user_id, grant_id):
    """Return True if user has role 'Co-PI' on this grant."""
    entry = GrantTeam.query.filter_by(
        user_id=user_id, grant_id=grant_id, role='Co-PI', status='active'
    ).first()
    return entry is not None

def has_budget_authority(user_id, grant_id):
    """Return True if user is Co-PI AND has budget_authority=True on this grant."""
    entry = GrantTeam.query.filter_by(
        user_id=user_id, grant_id=grant_id, role='Co-PI', status='active'
    ).first()
    return entry is not None and entry.budget_authority

def get_co_pi_count(grant_id):
    """Return the number of active Co-PIs on a grant."""
    return GrantTeam.query.filter_by(grant_id=grant_id, role='Co-PI', status='active').count()

def can_approve_deliverable(approver_id, deliverable, task):
    """
    Determine if a user can approve a deliverable submission.
    - PI of the grant can approve (but NOT their own submission).
    - Co-PI of the grant can always approve (including PI's submissions).
    - RSU can approve PI self-submissions on grants with no active Co-PI.
    Returns (allowed: bool, reason: str)
    """
    approver = User.query.get(approver_id)
    if not approver:
        return False, 'Approver not found'

    # Block self-approval (conflict of interest)
    if deliverable.user_id == approver_id:
        return False, 'Conflict of Interest: You cannot approve your own deliverable'

    if approver.role == 'RSU':
        grant = Grant.query.get(task.grant_id)
        if not grant:
            return False, 'Grant not found'
        if grant.pi_id != deliverable.user_id:
            return False, 'RSU only reviews Principal Investigator work'
        if get_co_pi_count(task.grant_id) > 0:
            return False, 'RSU approval blocked: This grant has a Co-PI who must review PI work first'
        return True, 'RSU fallback approval'

    grant = Grant.query.get(task.grant_id)
    if not grant:
        return False, 'Grant not found'

    # PI/Co-PI can approve team work
    submitter = User.query.get(deliverable.user_id)
    if submitter and submitter.role == 'Team':
        if (approver.role == 'PI' and grant.pi_id == approver_id) or is_co_pi(approver_id, task.grant_id):
            return True, 'PI/Co-PI approval'

    # Cross-PI / Co-PI Review
    if submitter and submitter.role == 'PI':
        if is_co_pi(approver_id, task.grant_id) or (approver.role == 'PI' and grant.pi_id == approver_id and deliverable.user_id != approver_id):
            return True, 'Cross-PI/Co-PI approval'

    return False, 'You do not have permission to approve this deliverable'

# Deliverable rules based on task type
DELIVERABLE_RULES = {
    'Fieldwork': ['Photo (with GPS/timestamp)', 'Written report'],
    'Data Analysis': ['Output files (.csv, .pdf, .xlsx)', 'Methodology notes'],
    'Remote Work': ['Activity log', 'Supporting documents'],
    'Reporting': ['Draft report', 'References']
}

@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    """
    Create a new task — only for logged-in PIs or Co-PIs.
    Requires: grant_id, assigned_to, title, task_type, deadline, estimated_hours
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    grant = Grant.query.get(grant_id)
    if not grant:
        return jsonify({'error': 'Grant not found'}), 404

    # Allow PI or Co-PI
    if user.role != 'PI' and not is_co_pi(user_id, grant_id):
        return jsonify({'error': 'Only PIs or Co-PIs can create tasks'}), 403

    # Ethics Compliance Lock (New)
    if grant.ethics_required and grant.ethics_status in ['PENDING_ETHICS', 'SUSPENDED_ETHICS']:
        status_display = "pending RSU verification" if grant.ethics_status == 'PENDING_ETHICS' else "suspended due to expiry"
        return jsonify({
            'error': f'Ethics Compliance Lock: This grant is currently {status_display}. Task creation is locked.',
            'type': 'ETHICS_LOCK',
            'ethics_status': grant.ethics_status
        }), 403

    try:
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        new_task = TaskService.create_task(data, user_id)
        
        # Log audit trail
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        audit_log = AuditLog(
            user_id=user_id,
            action='task_created',
            resource_type='task',
            resource_id=new_task.id,
            details=f'Task "{new_task.title}" assigned to {new_task.assignee.name} for grant "{new_task.grant.title}" from IP: {client_ip}'
        )
        db.session.add(audit_log)
        db.session.commit()

        task_dict = new_task.to_dict()
        task_dict['deliverable_rules'] = DELIVERABLE_RULES.get(new_task.task_type, [])
        task_dict['grant_title'] = new_task.grant.title
        task_dict['grant_code'] = new_task.grant.grant_code
        task_dict['assigned_to_name'] = new_task.assignee.name
        task_dict['assigned_to_email'] = new_task.assignee.email

        return jsonify(task_dict), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Task creation error: {str(e)}")
        return jsonify({'error': 'Failed to create task', 'details': str(e)}), 500

@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    Get tasks based on user role:
    - PI: All tasks for their grants
    - Team Member: Tasks assigned to them
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        tasks = TaskService.get_tasks_for_user(user_id, role=user.role)
        return jsonify({'tasks': tasks}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        return jsonify({'error': 'Failed to fetch tasks', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Update an existing task.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        updated_task = TaskService.update_task(task_id, data, user_id)
        
        # Log audit trail
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        audit_log = AuditLog(
            user_id=user_id,
            action='task_updated',
            resource_type='task',
            resource_id=task_id,
            details=f'Task "{updated_task.title}" updated by PI from IP: {client_ip}'
        )
        db.session.add(audit_log)
        db.session.commit()

        # Get enriched task data
        task_dict = TaskService.get_task_by_id(task_id)
        return jsonify(task_dict), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Task update error: {str(e)}")
        return jsonify({'error': 'Failed to update task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Delete a task.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        result = TaskService.delete_task(task_id, user_id)
        
        # Log audit trail
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        audit_log = AuditLog(
            user_id=user_id,
            action='task_deleted',
            resource_type='task',
            resource_id=task_id,
            details=f'Task deleted by PI from IP: {client_ip}'
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify(result), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Task deletion error: {str(e)}")
        return jsonify({'error': 'Failed to delete task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>/deliverables', methods=['POST'])
def submit_deliverable(task_id):
    """
    Submit deliverables for a task.
    Allowed: the user who is assigned to the task (Team, PI, or Co-PI self-tasks).
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        # Verify task exists and is assigned to this user
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        if task.assigned_to != user_id:
            return jsonify({'error': 'You can only submit deliverables for tasks assigned to you'}), 403

        # Ethics Compliance Lock (New)
        grant = Grant.query.get(task.grant_id)
        if grant and grant.ethics_required and grant.ethics_status in ['PENDING_ETHICS', 'SUSPENDED_ETHICS']:
            status_display = "pending RSU verification" if grant.ethics_status == 'PENDING_ETHICS' else "suspended due to expiry"
            return jsonify({
                'error': f'Ethics Compliance Lock: This grant is currently {status_display}. Deliverable submission is locked.',
                'type': 'ETHICS_LOCK',
                'ethics_status': grant.ethics_status
            }), 403

        # 3. Handle file uploads
        files = request.files.getlist('files')
        notes = request.form.get('notes', '').strip()
        hours_worked_raw = request.form.get('hours_worked')

        if not files and not notes:
            return jsonify({'error': 'Please provide deliverable files or notes'}), 400

        # Actual hours are sourced from submission; fallback to estimate when omitted.
        if hours_worked_raw is not None and str(hours_worked_raw).strip() != '':
            try:
                hours_worked = float(hours_worked_raw)
                if hours_worked < 0:
                    return jsonify({'error': 'hours_worked must be 0 or greater'}), 400
            except ValueError:
                return jsonify({'error': 'hours_worked must be a valid number'}), 400
        else:
            hours_worked = float(task.estimated_hours or 0.0)

        # 4. Save files
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'deliverables')
        os.makedirs(uploads_dir, exist_ok=True)
        
        file_paths = []
        for file in files:
            if file.filename:
                filename = f"deliverable_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(uploads_dir, filename)
                file.save(file_path)
                file_paths.append(filename)

        # 5. Check if there's an existing deliverable submission for this task
        existing_deliverable = DeliverableSubmission.query.filter_by(task_id=task_id).first()
        
        if existing_deliverable:
            # Append new files to existing ones
            existing_paths = existing_deliverable.document_paths.split(',') if existing_deliverable.document_paths else []
            all_paths = [p for p in existing_paths if p] + file_paths
            
            existing_deliverable.document_paths = ','.join(all_paths) if all_paths else None
            
            # Append notes if they exist
            if notes:
                if existing_deliverable.activity_notes:
                    existing_deliverable.activity_notes += f"\n\n[Resubmission Notes]: {notes}"
                else:
                    existing_deliverable.activity_notes = notes
            existing_deliverable.hours_worked = hours_worked
                    
            existing_deliverable.verification_status = 'pending'
            existing_deliverable.submitted_at = datetime.utcnow()
            deliverable = existing_deliverable
            action_message = 'Deliverables submitted and appended successfully'
        else:
            # Create new deliverable submission
            deliverable = DeliverableSubmission(
                task_id=task_id,
                user_id=user_id,
                hours_worked=hours_worked,
                document_paths=','.join(file_paths) if file_paths else None,
                activity_notes=notes,
                verification_status='pending'
            )
            db.session.add(deliverable)
            action_message = 'Deliverables submitted successfully'

        # 6. Update task status
        task.status = 'submitted'
        db.session.add(task)

        # 7. Log audit trail
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        audit_log = AuditLog(
            user_id=user_id,
            action='deliverables_submitted' if not existing_deliverable else 'deliverables_resubmitted',
            resource_type='task',
            resource_id=task_id,
            details=f'Deliverables {"resubmitted" if existing_deliverable else "submitted"} for task "{task.title}" by {user.name} from IP: {client_ip}'
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            'message': action_message,
            'task_id': task_id,
            'files_uploaded': len(file_paths),
            'is_resubmission': existing_deliverable is not None,
            'hours_worked': deliverable.hours_worked
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Deliverable submission error: {str(e)}")
        return jsonify({'error': 'Failed to submit deliverables', 'details': str(e)}), 500

@tasks_bp.route('/deliverables', methods=['GET'])
def get_deliverables():
    """
    Get deliverable submissions for grants owned by the PI.
    Filters: status (pending, approved, revision_requested)
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    status = (request.args.get('status') or 'pending').strip()

    try:
        # 1. PI Logic: See deliverables for grants they OWN
        # 2. Co-PI Logic: See deliverables for grants where they are Co-PI
        
        owned_grants = Grant.query.filter_by(pi_id=user_id).all()
        owned_grant_ids = [g.id for g in owned_grants]
        
        co_pi_entries = GrantTeam.query.filter_by(user_id=user_id, role='Co-PI', status='active').all()
        co_pi_grant_ids = [e.grant_id for e in co_pi_entries]
        
        all_reviewable_grant_ids = list(set(owned_grant_ids + co_pi_grant_ids))

        if user.role == 'RSU':
            # RSU only sees deliverables the grant PI submitted themselves (same rule as
            # can_approve_deliverable), on grants with no active Co-PI. Match by Grant.pi_id
            # so we do not depend on User.role string casing or stale role values.
            grants_with_any_co_pi = db.session.query(GrantTeam.grant_id).filter(
                GrantTeam.role == 'Co-PI',
                GrantTeam.status == 'active',
            ).distinct().all()
            excluded_grant_ids = [g[0] for g in grants_with_any_co_pi]

            query = (
                DeliverableSubmission.query.join(
                    Task, DeliverableSubmission.task_id == Task.id
                )
                .join(Grant, Task.grant_id == Grant.id)
                .filter(Grant.pi_id == DeliverableSubmission.user_id)
            )
            if excluded_grant_ids:
                query = query.filter(~Grant.id.in_(excluded_grant_ids))
        elif all_reviewable_grant_ids:
            # User is PI or Co-PI on some grants
            tasks_query = Task.query.filter(Task.grant_id.in_(all_reviewable_grant_ids))
            task_ids = [t.id for t in tasks_query.all()]
            query = DeliverableSubmission.query.filter(
                DeliverableSubmission.task_id.in_(task_ids),
                DeliverableSubmission.user_id != user_id  # Prevent self-approval
            )
        elif user.role == 'Team':
            # Regular Team: see only their own deliverables
            tasks_query = Task.query.filter_by(assigned_to=user_id)
            task_ids = [t.id for t in tasks_query.all()]
            query = DeliverableSubmission.query.filter(DeliverableSubmission.task_id.in_(task_ids))
        else:
            return jsonify({'error': 'Unauthorized role or no reviewable grants'}), 403

        status_lc = status.lower() if status else ''
        if status_lc:
            query = query.filter(
                func.lower(
                    func.coalesce(DeliverableSubmission.verification_status, 'pending')
                )
                == status_lc
            )
        
        submissions = query.order_by(DeliverableSubmission.submitted_at.desc()).all()

        results = []
        for deliverable in submissions:
            task = Task.query.get(deliverable.task_id)
            if not task:
                print(f"Warning: Deliverable {deliverable.id} orphan - task {deliverable.task_id} missing")
                continue
                
            assignee = User.query.get(task.assigned_to)
            
            # Format documents list
            docs = []
            if deliverable.document_paths:
                # Handle both comma-separated and potentially JSON (if that comment was right)
                paths = []
                if deliverable.document_paths.startswith('['):
                    import json
                    try:
                        paths = json.loads(deliverable.document_paths)
                    except:
                        paths = deliverable.document_paths.split(',')
                else:
                    paths = deliverable.document_paths.split(',')
                    
                for path in paths:
                    if path:
                        docs.append({
                            'name': path.split('_')[-1], # Show original filename part
                            'url': f"http://localhost:5000/api/uploads/deliverables/{path}"
                        })

            results.append({
                'id': deliverable.id,
                'task_id': task.id,
                'task_title': task.title,
                'grant_title': task.grant.title if task.grant else 'Unknown Grant',
                'team_member': assignee.name if assignee else 'Unknown Assignee',
                'submitted_at': deliverable.submitted_at.isoformat() if deliverable.submitted_at else None,
                'task_start': task.created_at.isoformat() if task.created_at else None,
                'task_end': task.deadline.isoformat() if task.deadline else None,
                'hours_worked': deliverable.hours_worked,
                'notes': deliverable.activity_notes,
                'status': deliverable.verification_status,
                'photo_url': f"http://localhost:5000/api/uploads/deliverables/{deliverable.photo_path}" if deliverable.photo_path else None,
                'documents': docs,
                'is_pi_submission': assignee.role == 'PI' if assignee else False,
                'submitted_by_role': assignee.role if assignee else 'Unknown',
                'unreturned_assets': Asset.query.filter_by(assigned_task_id=task.id, status='ACTIVE').count() if task else 0
            })

        return jsonify({'submissions': results}), 200

    except Exception as e:
        import traceback
        print(f"Error fetching deliverables: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch deliverables', 'details': str(e)}), 500

@tasks_bp.route('/deliverables/<int:id>/approve', methods=['POST'])
def approve_deliverable(id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        deliverable = DeliverableSubmission.query.get(id)
        if not deliverable:
            return jsonify({'error': 'Deliverable not found'}), 404

        task = Task.query.get(deliverable.task_id)
        allowed, reason = can_approve_deliverable(user_id, deliverable, task)
        if not allowed:
            return jsonify({'error': reason}), 403

        deliverable = TaskService.verify_deliverable(id, 'approved', user_id)

        # Audit log for PI self-submission approval (flags for audit)
        submitter = User.query.get(deliverable.user_id)
        if submitter and submitter.role == 'PI':
            audit = AuditLog(
                user_id=user_id,
                action='pi_deliverable_approved',
                resource_type='deliverable',
                resource_id=id,
                details=f'PI self-submission approved. Submitter: {submitter.name}. Approver role: {User.query.get(user_id).role}. self_attested=True'
            )
            db.session.add(audit)
            db.session.commit()

        return jsonify({'message': 'Deliverable approved', 'status': deliverable.verification_status}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500

@tasks_bp.route('/deliverables/<int:id>/request-revision', methods=['POST'])
def request_revision(id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    comment = data.get('comment')

    try:
        deliverable = DeliverableSubmission.query.get(id)
        if not deliverable:
            return jsonify({'error': 'Deliverable not found'}), 404

        task = Task.query.get(deliverable.task_id)
        allowed, reason = can_approve_deliverable(user_id, deliverable, task)
        if not allowed:
            return jsonify({'error': reason}), 403

        deliverable = TaskService.verify_deliverable(id, 'revision_requested', user_id, notes=comment)
        return jsonify({'message': 'Revision requested', 'status': deliverable.verification_status}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@tasks_bp.route('/team-members', methods=['GET'])
def get_team_members():
    """
    Get all users available to be assigned tasks:
    - Team Members across all of PI's grants
    - The PI themselves (for self-assigned tasks)
    - Co-PIs on the PI's grants
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'PI':
        return jsonify({'error': 'Only PIs can view team members'}), 403

    try:
        # Get all grants this PI owns
        grants = Grant.query.filter_by(pi_id=user_id).all()
        grant_ids = [g.id for g in grants]

        # Collect all team member user IDs (including Co-PIs)
        team_entries = GrantTeam.query.filter(
            GrantTeam.grant_id.in_(grant_ids), GrantTeam.status == 'active'
        ).all()
        team_user_ids = list(set([e.user_id for e in team_entries]))

        # Also include the PI themselves as an assignable person
        if user_id not in team_user_ids:
            team_user_ids.append(user_id)

        members = []
        for uid in team_user_ids:
            u = User.query.get(uid)
            if u:
                # Find what grant-level role this user has
                entry = GrantTeam.query.filter(
                    GrantTeam.user_id == uid,
                    GrantTeam.grant_id.in_(grant_ids)
                ).first()
                grant_level_role = entry.role if entry else (u.role if u.id == user_id else 'Member')
                members.append({
                    'id': u.id,
                    'name': u.name + (' (You)' if u.id == user_id else ''),
                    'email': u.email,
                    'role': u.role,
                    'grant_level_role': grant_level_role,
                    'is_self': u.id == user_id
                })

        return jsonify({'team_members': members}), 200

    except Exception as e:
        print(f"Error fetching team members: {str(e)}")
        return jsonify({'error': 'Failed to fetch team members'}), 500



