# routes/asset_assignments.py
"""Asset Assignment Routes - Task-Linked Asset Management"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_assignment_service import AssetAssignmentService
from werkzeug.utils import secure_filename
import os
from datetime import datetime

asset_assignments_bp = Blueprint('asset_assignments', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@asset_assignments_bp.route('/asset-assignments/task/<int:task_id>', methods=['POST'])
@token_required
def create_asset_assignment(user, task_id):
    """Create asset requirement for task"""
    try:
        data = request.get_json()
        asset_requirements = data.get('asset_requirements', [])
        
        if not asset_requirements:
            return jsonify({'error': 'No asset requirements provided'}), 400
        
        assignments = AssetAssignmentService.request_assets_for_task(
            task_id, asset_requirements, user.id
        )
        
        return jsonify({
            'message': f'Created {len(assignments)} asset assignments',
            'assignments': [assignment.to_dict() for assignment in assignments]
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create asset assignments', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/<int:assignment_id>/pickup', methods=['PUT'])
@token_required
def confirm_pickup(user, assignment_id):
    """Confirm asset pickup by team member"""
    try:
        # Handle file upload for evidence
        evidence_doc = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"pickup_{assignment_id}_{timestamp}_{filename}"
                
                upload_path = os.path.join(UPLOAD_FOLDER, 'asset_evidence')
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)
                evidence_doc = file_path
        
        assignment = AssetAssignmentService.confirm_asset_pickup(
            assignment_id, user.id, evidence_doc
        )
        
        return jsonify({
            'message': 'Asset pickup confirmed',
            'assignment': assignment.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to confirm pickup', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/<int:assignment_id>/return', methods=['PUT'])
@token_required
def confirm_return(user, assignment_id):
    """Confirm asset return"""
    try:
        # Handle file upload for evidence
        evidence_doc = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"return_{assignment_id}_{timestamp}_{filename}"
                
                upload_path = os.path.join(UPLOAD_FOLDER, 'asset_evidence')
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)
                evidence_doc = file_path
        
        assignment = AssetAssignmentService.confirm_asset_return(
            assignment_id, user.id, evidence_doc
        )
        
        return jsonify({
            'message': 'Asset return confirmed',
            'assignment': assignment.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to confirm return', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/user/pending', methods=['GET'])
@token_required
def get_user_pending_assignments(user):
    """Get assets user needs to return"""
    try:
        pending_assignments = AssetAssignmentService.get_pending_returns_for_user(user.id)
        
        return jsonify({
            'pending_assignments': [assignment.to_dict() for assignment in pending_assignments],
            'count': len(pending_assignments)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get pending assignments', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/task/<int:task_id>/status', methods=['GET'])
@token_required
def get_task_asset_status(user, task_id):
    """Check if all task assets are returned"""
    try:
        can_complete = AssetAssignmentService.can_complete_task(task_id)
        pending_returns = AssetAssignmentService.get_pending_returns_for_task(task_id)
        
        return jsonify({
            'can_complete_task': can_complete,
            'pending_returns': [assignment.to_dict() for assignment in pending_returns],
            'pending_count': len(pending_returns)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get task asset status', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/task/<int:task_id>', methods=['GET'])
@token_required
def get_task_assignments(user, task_id):
    """Get all asset assignments for a task"""
    try:
        assignments = AssetAssignmentService.get_task_asset_assignments(task_id)
        
        return jsonify({
            'assignments': [assignment.to_dict() for assignment in assignments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get task assignments', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/user/history', methods=['GET'])
@token_required
def get_user_assignment_history(user):
    """Get assignment history for current user"""
    try:
        assignments = AssetAssignmentService.get_user_assignment_history(user.id)
        
        return jsonify({
            'assignments': [assignment.to_dict() for assignment in assignments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get assignment history', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/available/grant/<int:grant_id>', methods=['GET'])
@token_required
def get_available_assets_for_grant(user, grant_id):
    """Get available assets for a grant"""
    try:
        assets = AssetAssignmentService.get_available_assets_for_grant(grant_id)
        
        return jsonify({
            'available_assets': [asset.to_dict() for asset in assets]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get available assets', 'details': str(e)}), 500

@asset_assignments_bp.route('/asset-assignments/<int:assignment_id>', methods=['GET'])
@token_required
def get_assignment_details(user, assignment_id):
    """Get details of a specific assignment"""
    try:
        from models import AssetAssignment
        assignment = AssetAssignment.query.get(assignment_id)
        
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Check if user has permission to view this assignment
        if (assignment.assigned_to_user_id != user.id and 
            assignment.task.grant.pi_id != user.id):
            return jsonify({'error': 'Permission denied'}), 403
        
        return jsonify({
            'assignment': assignment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get assignment details', 'details': str(e)}), 500
