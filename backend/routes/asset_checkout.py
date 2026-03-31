# routes/asset_checkout.py
"""Asset Checkout Routes - Phase 2: Planning Core
API endpoints for asset checkout, reservation, and management"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_assignment_service import AssetAssignmentService
from werkzeug.utils import secure_filename
import os
from datetime import datetime

asset_checkout_bp = Blueprint('asset_checkout', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@asset_checkout_bp.route('/asset-checkout/milestone/<int:milestone_id>/reserve', methods=['POST'])
@token_required
def reserve_milestone_assets(user, milestone_id):
    """Reserve assets for an upcoming milestone"""
    try:
        data = request.get_json()
        asset_requirements = data.get('asset_requirements', [])
        
        if not asset_requirements:
            return jsonify({'error': 'Asset requirements are required'}), 400
        
        # Check user permissions
        from models import Milestone
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        if milestone.grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        reservations = AssetAssignmentService.reserve_assets_for_milestone(
            milestone_id, asset_requirements, user.id
        )
        
        return jsonify({
            'message': f'Created {len(reservations)} asset reservations',
            'reservations': [r.to_dict() for r in reservations],
            'milestone_id': milestone_id,
            'milestone_title': milestone.title
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to reserve assets', 'details': str(e)}), 500

@asset_checkout_bp.route('/asset-checkout/assignment/<int:assignment_id>/checkout', methods=['PUT'])
@token_required
def checkout_asset(user, assignment_id):
    """Check out asset to specific user with evidence"""
    try:
        # Handle file upload for pickup evidence
        pickup_evidence = None
        if 'pickup_evidence' in request.files:
            file = request.files['pickup_evidence']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"pickup_{assignment_id}_{timestamp}_{filename}"
                
                upload_path = os.path.join(UPLOAD_FOLDER, 'asset_evidence')
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)
                pickup_evidence = file_path
        
        assignment = AssetAssignmentService.checkout_asset_to_user(
            assignment_id, user.id, pickup_evidence
        )
        
        return jsonify({
            'message': 'Asset checked out successfully',
            'assignment': assignment.to_dict(),
            'pickup_evidence': pickup_evidence
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to checkout asset', 'details': str(e)}), 500

@asset_checkout_bp.route('/asset-checkout/user/<int:user_id>/history', methods=['GET'])
@token_required
def get_user_checkout_history(user, user_id):
    """Get checkout history for a user"""
    try:
        # Check permissions (users can only see their own history, RSU can see all)
        if user.id != user_id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        history = AssetAssignmentService.get_user_asset_checkout_history(
            user_id, start_dt, end_dt
        )
        
        return jsonify({
            'user_id': user_id,
            'checkout_history': [h.to_dict() for h in history],
            'total_checkouts': len(history),
            'period': {
                'start': start_date,
                'end': end_date
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get checkout history', 'details': str(e)}), 500

@asset_checkout_bp.route('/asset-checkout/asset/<int:asset_id>/statistics', methods=['GET'])
@token_required
def get_asset_checkout_statistics(user, asset_id):
    """Get checkout statistics for a specific asset"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert to datetime if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        stats = AssetAssignmentService.get_asset_checkout_statistics(
            asset_id, start_dt, end_dt
        )
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get checkout statistics', 'details': str(e)}), 500

@asset_checkout_bp.route('/asset-checkout/active', methods=['GET'])
@token_required
def get_active_checkouts(user):
    """Get all currently checked out assets"""
    try:
        from models import AssetAssignment
        active_assignments = AssetAssignment.query.filter_by(status='ASSIGNED').all()
        
        active_checkouts = []
        for assignment in active_assignments:
            checkout_data = assignment.to_dict()
            
            # Add asset information
            if assignment.asset:
                checkout_data['asset_name'] = assignment.asset.name
                checkout_data['asset_category'] = assignment.asset.category
                checkout_data['asset_specifications'] = assignment.asset.specifications or {}
            
            # Add user information
            if assignment.assigned_user:
                checkout_data['user_name'] = assignment.assigned_user.name
                checkout_data['user_email'] = assignment.assigned_user.email
            
            # Add task information
            if assignment.task:
                checkout_data['task_title'] = assignment.task.title
                checkout_data['milestone_title'] = assignment.task.milestone.title if assignment.task.milestone else None
            
            active_checkouts.append(checkout_data)
        
        return jsonify({
            'active_checkouts': active_checkouts,
            'total_active': len(active_checkouts)
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get active checkouts', 'details': str(e)}), 500

@asset_checkout_bp.route('/asset-checkout/overdue', methods=['GET'])
@token_required
def get_overdue_checkouts(user):
    """Get overdue asset checkouts"""
    try:
        from models import AssetAssignment
        from datetime import datetime, timedelta
        
        # Define overdue threshold (7 days past assigned date)
        overdue_threshold = datetime.utcnow() - timedelta(days=7)
        
        overdue_assignments = AssetAssignment.query.filter(
            AssetAssignment.status == 'ASSIGNED',
            AssetAssignment.assigned_at <= overdue_threshold
        ).all()
        
        overdue_checkouts = []
        for assignment in overdue_assignments:
            overdue_data = assignment.to_dict()
            
            # Calculate days overdue
            days_overdue = (datetime.utcnow() - assignment.assigned_at).days
            overdue_data['days_overdue'] = days_overdue
            overdue_data['overdue_since'] = assignment.assigned_at.isoformat()
            
            # Add asset and user info
            if assignment.asset:
                overdue_data['asset_name'] = assignment.asset.name
                overdue_data['asset_category'] = assignment.asset.category
            
            if assignment.assigned_user:
                overdue_data['user_name'] = assignment.assigned_user.name
                overdue_data['user_email'] = assignment.assigned_user.email
            
            if assignment.task:
                overdue_data['task_title'] = assignment.task.title
                overdue_data['milestone_title'] = assignment.task.milestone.title if assignment.task.milestone else None
            
            overdue_checkouts.append(overdue_data)
        
        return jsonify({
            'overdue_checkouts': overdue_checkouts,
            'total_overdue': len(overdue_checkouts),
            'overdue_threshold_days': 7,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get overdue checkouts', 'details': str(e)}), 500
