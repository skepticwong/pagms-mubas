# routes/analytics.py
"""Analytics Routes - Asset Utilization and Performance Metrics"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_assignment_service import AssetAssignmentService

analytics_bp = Blueprint('asset_analytics', __name__)

@analytics_bp.route('/analytics/asset-utilization/<int:grant_id>', methods=['GET'])
@token_required
def get_asset_utilization_metrics(user, grant_id):
    """Get asset utilization metrics for a grant"""
    try:
        # Get date range from query params
        date_range = request.args.get('range', 'all')
        
        metrics = AssetAssignmentService.get_asset_utilization_metrics(
            grant_id, 
            start_date=None if date_range == 'all' else request.args.get('start_date'),
            end_date=None if date_range == 'all' else request.args.get('end_date')
        )
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to load asset utilization metrics',
            'details': str(e)
        }), 500

@analytics_bp.route('/analytics/missing-assets/<int:grant_id>', methods=['GET'])
@token_required
def get_missing_assets_alert(user, grant_id):
    """Get missing assets alert for a grant"""
    try:
        from models import Grant
        
        # Check if user has permission to view grant analytics
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
            
        if grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get utilization metrics to extract missing assets
        metrics = AssetAssignmentService.get_asset_utilization_metrics(grant_id)
        
        return jsonify({
            'missing_asset_risk': metrics['missing_asset_risk'],
            'missing_assets': []  # This would be populated with actual asset details
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get missing assets',
            'details': str(e)
        }), 500

@analytics_bp.route('/analytics/task-coverage/<int:grant_id>', methods=['GET'])
@token_required
def get_task_coverage_metrics(user, grant_id):
    """Get task coverage metrics for a grant"""
    try:
        from models import Grant
        
        # Check if user has permission to view grant analytics
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
            
        if grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get utilization metrics
        metrics = AssetAssignmentService.get_asset_utilization_metrics(grant_id)
        
        return jsonify({
            'total_tasks': metrics['total_tasks'],
            'tasks_with_assets': metrics['tasks_with_assets'],
            'task_coverage_percentage': metrics['asset_utilization_rate'],
            'total_assignments': metrics['total_assignments'],
            'returned_assignments': metrics['returned_assignments'],
            'pending_assignments': metrics['total_assignments'] - metrics['returned_assignments']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get task coverage metrics',
            'details': str(e)
        }), 500
