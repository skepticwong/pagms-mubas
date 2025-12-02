from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, date
from models import db, Task, Grant, User, AuditLog, EvidenceSubmission
import os
from services.task_service import TaskService # Import the TaskService

tasks_bp = Blueprint('tasks', __name__)
CORS(tasks_bp, origins=["http://localhost:5173"], supports_credentials=True)

# Evidence rules based on task type
EVIDENCE_RULES = {
    'Fieldwork': ['Photo (with GPS/timestamp)', 'Written report'],
    'Data Analysis': ['Output files (.csv, .pdf, .xlsx)', 'Methodology notes'],
    'Remote Work': ['Activity log', 'Supporting documents'],
    'Reporting': ['Draft report', 'References']
}

@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    """
    Create a new task — only for logged-in PIs.
    Requires: grant_id, assigned_to, title, task_type, deadline, estimated_hours
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'PI':
        return jsonify({'error': 'Only PIs can create tasks'}), 403

    try:
        data = request.get_json()
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
        task_dict['evidence_rules'] = EVIDENCE_RULES.get(new_task.task_type, [])
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

@tasks_bp.route('/tasks/<int:task_id>/evidence', methods=['POST'])
def submit_evidence(task_id):
    """
    Submit evidence for a task — only for assigned Team Member.
    """
    # 1. Verify user is authenticated
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Team':
        return jsonify({'error': 'Only Team Members can submit evidence'}), 403

    try:
        # 2. Verify task exists and is assigned to this user
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        if task.assigned_to != user_id:
            return jsonify({'error': 'You can only submit evidence for tasks assigned to you'}), 403

        # 3. Handle file uploads
        files = request.files.getlist('files')
        notes = request.form.get('notes', '').strip()

        if not files and not notes:
            return jsonify({'error': 'Please provide evidence files or notes'}), 400

        # 4. Save files
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'evidence')
        os.makedirs(uploads_dir, exist_ok=True)
        
        file_paths = []
        for file in files:
            if file.filename:
                filename = f"evidence_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(uploads_dir, filename)
                file.save(file_path)
                file_paths.append(filename)

        # 5. Check if there's an existing evidence submission for this task
        existing_evidence = EvidenceSubmission.query.filter_by(task_id=task_id).first()
        
        if existing_evidence:
            # Update existing evidence (resubmission after revision request)
            existing_evidence.document_paths = ','.join(file_paths) if file_paths else existing_evidence.document_paths
            existing_evidence.activity_notes = notes if notes else existing_evidence.activity_notes
            existing_evidence.verification_status = 'pending'
            existing_evidence.submitted_at = datetime.utcnow()
            evidence = existing_evidence
            action_message = 'Evidence resubmitted successfully'
        else:
            # Create new evidence submission
            evidence = EvidenceSubmission(
                task_id=task_id,
                hours_worked=task.estimated_hours,  # Default to estimated, can be updated
                document_paths=','.join(file_paths) if file_paths else None,
                activity_notes=notes,
                verification_status='pending'
            )
            db.session.add(evidence)
            action_message = 'Evidence submitted successfully'

        # 6. Update task status
        task.status = 'submitted'
        db.session.add(task)

        # 7. Log audit trail
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        audit_log = AuditLog(
            user_id=user_id,
            action='evidence_submitted' if not existing_evidence else 'evidence_resubmitted',
            resource_type='task',
            resource_id=task_id,
            details=f'Evidence {"resubmitted" if existing_evidence else "submitted"} for task "{task.title}" by {user.name} from IP: {client_ip}'
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            'message': action_message,
            'task_id': task_id,
            'files_uploaded': len(file_paths),
            'is_resubmission': existing_evidence is not None
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Evidence submission error: {str(e)}")
        return jsonify({'error': 'Failed to submit evidence', 'details': str(e)}), 500

@tasks_bp.route('/evidence', methods=['GET'])
def get_evidence():
    """
    Get evidence submissions for grants owned by the PI.
    Filters: status (pending, approved, revision_requested)
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    status = request.args.get('status', 'pending')

    try:
        if user.role == 'PI':
            # Get all grants owned by PI
            grants = Grant.query.filter_by(pi_id=user_id).all()
            grant_ids = [g.id for g in grants]
            
            # Get all tasks for these grants
            tasks_query = Task.query.filter(Task.grant_id.in_(grant_ids))
            task_ids = [t.id for t in tasks_query.all()]
            
            # Get evidence submissions for these tasks
            query = EvidenceSubmission.query.filter(EvidenceSubmission.task_id.in_(task_ids))
        elif user.role == 'Team':
            # Team members see only THEIR OWN evidence
            tasks_query = Task.query.filter_by(assigned_to=user_id)
            task_ids = [t.id for t in tasks_query.all()]
            query = EvidenceSubmission.query.filter(EvidenceSubmission.task_id.in_(task_ids))
        else:
            return jsonify({'error': 'Unauthorized role'}), 403
        if status:
            query = query.filter(EvidenceSubmission.verification_status == status)
        
        submissions = query.order_by(EvidenceSubmission.submitted_at.desc()).all()

        results = []
        for evidence in submissions:
            task = Task.query.get(evidence.task_id)
            assignee = User.query.get(task.assigned_to)
            
            # Format documents list
            docs = []
            if evidence.document_paths:
                for path in evidence.document_paths.split(','):
                    if path:
                        docs.append({
                            'name': path.split('_')[-1], # Show original filename part
                            'url': f"http://localhost:5000/api/uploads/evidence/{path}"
                        })

            results.append({
                'id': evidence.id,
                'task_id': task.id,
                'task_title': task.title,
                'grant_title': task.grant.title,
                'team_member': assignee.name if assignee else 'Unknown',
                'submitted_at': evidence.submitted_at.isoformat() if evidence.submitted_at else None,
                'task_start': task.created_at.isoformat() if task.created_at else None, # Placeholder for window
                'task_end': task.deadline.isoformat() if task.deadline else None,
                'hours_worked': evidence.hours_worked,
                'notes': evidence.activity_notes,
                'status': evidence.verification_status,
                'photo_url': f"http://localhost:5000/api/uploads/evidence/{evidence.photo_path}" if evidence.photo_path else None,
                'documents': docs
            })

        return jsonify({'submissions': results}), 200

    except Exception as e:
        print(f"Error fetching evidence: {str(e)}")
        return jsonify({'error': 'Failed to fetch evidence', 'details': str(e)}), 500

@tasks_bp.route('/evidence/<int:id>/approve', methods=['POST'])
def approve_evidence(id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        evidence = TaskService.verify_evidence(id, 'approved', user_id)
        return jsonify({'message': 'Evidence approved', 'status': evidence.verification_status}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500

@tasks_bp.route('/evidence/<int:id>/request-revision', methods=['POST'])
def request_revision(id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    comment = data.get('comment')

    try:
        evidence = TaskService.verify_evidence(id, 'revision_requested', user_id, notes=comment)
        return jsonify({'message': 'Revision requested', 'status': evidence.verification_status}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@tasks_bp.route('/team-members', methods=['GET'])
def get_team_members():
    """
    Get all Team Members for PI to assign tasks.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'PI':
        return jsonify({'error': 'Only PIs can view team members'}), 403

    try:
        team_members = TaskService.get_team_members_for_pi(user_id)
        return jsonify({'team_members': team_members}), 200

    except Exception as e:
        print(f"Error fetching team members: {str(e)}")
        return jsonify({'error': 'Failed to fetch team members'}), 500



