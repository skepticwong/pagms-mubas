# routes/grant_kpis.py
"""Grant KPI Routes - Phase 1: Grant-Level KPI Management
API endpoints for managing grant-level Key Performance Indicators"""

from flask import Blueprint, request, jsonify, session
from services.grant_kpi_service import GrantKPIService
from models import Grant, User

grant_kpis_bp = Blueprint('grant_kpis', __name__)

# Grant KPI Management (Grant Initialization Phase)

@grant_kpis_bp.route('/grant-kpis/grant/<int:grant_id>', methods=['POST'])
def create_grant_kpis(grant_id):
    """Create master KPI list for grant during initialization"""
    try:
        # Check user permissions
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user is PI or RSU
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        kpis_data = data.get('kpis', [])
        
        if not kpis_data:
            return jsonify({'error': 'No KPIs provided'}), 400
        
        result = GrantKPIService.create_grant_kpis(grant_id, kpis_data, user_id)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to create grant KPIs', 'details': str(e)}), 500

@grant_kpis_bp.route('/grant-kpis/grant/<int:grant_id>', methods=['GET'])
def get_grant_kpis(grant_id):
    """Get all master KPIs for a grant"""
    try:
        # Check user permissions
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user is PI or RSU
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        result = GrantKPIService.get_grant_kpis(grant_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to get grant KPIs', 'details': str(e)}), 500

@grant_kpis_bp.route('/grant-kpis/<int:kpi_id>', methods=['PUT'])
def update_grant_kpi(kpi_id):
    """Update grant KPI (admin only)"""
    try:
        # Check user permissions (admin only)
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        kpi_data = request.get_json()
        
        result = GrantKPIService.update_grant_kpi(kpi_id, kpi_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to update grant KPI', 'details': str(e)}), 500

@grant_kpis_bp.route('/grant-kpis/<int:kpi_id>', methods=['DELETE'])
def delete_grant_kpi(kpi_id):
    """Delete grant KPI (admin only)"""
    try:
        # Check user permissions (admin only)
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        result = GrantKPIService.delete_grant_kpi(kpi_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to delete grant KPI', 'details': str(e)}), 500

# Grant Progress & Reporting

@grant_kpis_bp.route('/grant-kpis/grant/<int:grant_id>/progress', methods=['GET'])
def get_grant_progress(grant_id):
    """Calculate overall grant achievement across all KPIs"""
    try:
        # Check user permissions
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user is PI or RSU
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        result = GrantKPIService.get_grant_progress(grant_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to calculate grant progress', 'details': str(e)}), 500

# Milestone Allocation Support

@grant_kpis_bp.route('/grant-kpis/available/<int:grant_id>', methods=['GET'])
def get_available_grant_kpis(grant_id):
    """Get master KPIs that can be allocated to milestones"""
    try:
        # Check user permissions
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user is PI or RSU
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        result = GrantKPIService.get_available_grant_kpis(grant_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to get available grant KPIs', 'details': str(e)}), 500

@grant_kpis_bp.route('/grant-kpis/allocate', methods=['POST'])
def allocate_kpi_to_milestone():
    """Allocate portion of grant KPI to milestone"""
    try:
        # Check user permissions
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        grant_kpi_id = data.get('grant_kpi_id')
        milestone_id = data.get('milestone_id')
        milestone_target = data.get('milestone_target')
        
        if not all([grant_kpi_id, milestone_id, milestone_target]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify milestone belongs to user's grant
        from models import Milestone
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        grant = Grant.query.get(milestone.grant_id)
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        result = GrantKPIService.allocate_kpi_to_milestone(grant_kpi_id, milestone_id, milestone_target)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to allocate KPI to milestone', 'details': str(e)}), 500

@grant_kpis_bp.route('/grant-kpis/allocation/<int:milestone_kpi_id>', methods=['DELETE'])
def remove_kpi_allocation(milestone_kpi_id):
    """Remove KPI allocation from milestone"""
    try:
        # Check user permissions
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Verify allocation belongs to user's milestone
        from models import MilestoneKPI
        allocation = MilestoneKPI.query.get(milestone_kpi_id)
        if not allocation:
            return jsonify({'error': 'KPI allocation not found'}), 404
        
        milestone = allocation.milestone
        grant = Grant.query.get(milestone.grant_id)
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        result = GrantKPIService.remove_kpi_allocation(milestone_kpi_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to remove KPI allocation', 'details': str(e)}), 500
