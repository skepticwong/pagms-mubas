# routes/asset_conflicts.py
"""Asset Conflict Detection Routes - Phase 2: Planning Core
API endpoints for detecting and resolving asset conflicts"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_conflict_service import AssetConflictService

asset_conflicts_bp = Blueprint('asset_conflicts', __name__)

@asset_conflicts_bp.route('/asset-conflicts/milestone/<int:milestone_id>', methods=['GET'])
@token_required
def check_milestone_conflicts(user, milestone_id):
    """Check for asset conflicts during milestone period"""
    try:
        from models import Milestone
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Check user permissions
        if milestone.grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        conflicts = AssetConflictService.check_asset_conflicts(
            milestone_id, milestone.start_date, milestone.end_date
        )
        
        return jsonify({
            'milestone_id': milestone_id,
            'milestone_title': milestone.title,
            'conflicts': conflicts,
            'total_conflicts': len(conflicts),
            'has_conflicts': len(conflicts) > 0
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to check conflicts', 'details': str(e)}), 500

@asset_conflicts_bp.route('/asset-conflicts/milestone/<int:milestone_id>/report', methods=['GET'])
@token_required
def get_conflict_report(user, milestone_id):
    """Generate comprehensive conflict report for milestone"""
    try:
        # Check user permissions
        from models import Milestone
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        if milestone.grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        report = AssetConflictService.generate_conflict_report(milestone_id)
        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': 'Failed to generate conflict report', 'details': str(e)}), 500

@asset_conflicts_bp.route('/asset-conflicts/asset/<int:asset_id>/availability', methods=['POST'])
@token_required
def check_asset_availability(user, asset_id):
    """Check if specific asset is available during time period"""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Convert string dates to datetime objects
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        is_available = AssetConflictService.check_asset_availability(
            asset_id, start_dt, end_dt
        )
        
        return jsonify({
            'asset_id': asset_id,
            'is_available': is_available,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'message': 'Asset is available' if is_available else 'Asset has conflicting assignments'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to check availability', 'details': str(e)}), 500

@asset_conflicts_bp.route('/asset-conflicts/asset/<int:asset_id>/schedule', methods=['POST'])
@token_required
def get_asset_utilization_schedule(user, asset_id):
    """Get detailed utilization schedule for an asset"""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Convert string dates to datetime objects
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        schedule = AssetConflictService.get_asset_utilization_schedule(
            asset_id, start_dt, end_dt
        )
        
        return jsonify({
            'asset_id': asset_id,
            'schedule': schedule,
            'total_assignments': len(schedule),
            'period': {
                'start': start_date,
                'end': end_date
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get schedule', 'details': str(e)}), 500

@asset_conflicts_bp.route('/asset-conflicts/suggestions/<int:milestone_id>', methods=['GET'])
@token_required
def get_conflict_suggestions(user, milestone_id):
    """Get resolution suggestions for detected conflicts"""
    try:
        from models import Milestone
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Check user permissions
        if milestone.grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get conflicts first
        conflicts = AssetConflictService.check_asset_conflicts(
            milestone_id, milestone.start_date, milestone.end_date
        )
        
        if not conflicts:
            return jsonify({
                'milestone_id': milestone_id,
                'suggestions': [],
                'message': 'No conflicts to resolve'
            }), 200
        
        # Get suggestions
        suggestions = AssetConflictService.get_conflict_resolution_suggestions(conflicts)
        
        return jsonify({
            'milestone_id': milestone_id,
            'conflicts_count': len(conflicts),
            'suggestions': suggestions,
            'recommendations': [
                'Review alternative assets suggested',
                'Consider adjusting milestone dates',
                'Contact RSU for additional equipment'
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get suggestions', 'details': str(e)}), 500

@asset_conflicts_bp.route('/asset-conflicts/grant/<int:grant_id>/overview', methods=['GET'])
@token_required
def get_grant_conflict_overview(user, grant_id):
    """Get conflict overview for all milestones in a grant"""
    try:
        # Check user permissions
        from models import Grant, Milestone
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        if grant.pi_id != user.id and user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get all milestones for the grant
        milestones = Milestone.query.filter_by(grant_id=grant_id).all()
        
        overview = {
            'grant_id': grant_id,
            'grant_title': grant.title,
            'total_milestones': len(milestones),
            'milestones_with_conflicts': 0,
            'total_conflicts': 0,
            'high_priority_conflicts': 0,
            'milestones': []
        }
        
        for milestone in milestones:
            conflicts = AssetConflictService.check_asset_conflicts(
                milestone.id, milestone.start_date, milestone.end_date
            )
            
            milestone_data = {
                'milestone_id': milestone.id,
                'title': milestone.title,
                'status': milestone.status,
                'start_date': milestone.start_date.isoformat(),
                'end_date': milestone.end_date.isoformat(),
                'conflicts_count': len(conflicts),
                'has_conflicts': len(conflicts) > 0
            }
            
            if len(conflicts) > 0:
                overview['milestones_with_conflicts'] += 1
                overview['total_conflicts'] += len(conflicts)
                
                # Count high priority conflicts (more than 3 conflicts)
                if len(conflicts) > 3:
                    overview['high_priority_conflicts'] += 1
            
            overview['milestones'].append(milestone_data)
        
        # Calculate conflict percentage
        if overview['total_milestones'] > 0:
            overview['conflict_percentage'] = round(
                (overview['milestones_with_conflicts'] / overview['total_milestones']) * 100, 1
            )
        else:
            overview['conflict_percentage'] = 0
        
        return jsonify(overview), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get conflict overview', 'details': str(e)}), 500
