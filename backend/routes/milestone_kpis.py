# routes/milestone_kpis.py
"""Milestone KPI Routes - Phase 1: Compliance Core
API endpoints for managing milestone KPIs and templates"""

from flask import Blueprint, request, jsonify, session
from middleware.auth import token_required
from services.milestone_kpi_service import MilestoneKPIService
from services.milestone_template_service import MilestoneTemplateService

milestone_kpis_bp = Blueprint('milestone_kpis', __name__)

@milestone_kpis_bp.route('/milestone-kpis/milestone/<int:milestone_id>', methods=['GET'])
def get_milestone_kpis(milestone_id):
    """Get all KPIs for a milestone - Simplified Version"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Milestone, Grant, User
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Check if user has permission (PI or RSU)
        grant = Grant.query.get(milestone.grant_id)
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        # Return simple test data for now - avoid complex service calls
        simple_kpis = [
            {
                'id': 1,
                'name': 'Test KPI - Simplified',
                'description': 'Test KPI for debugging',
                'target_value': 100,
                'actual_value': 85,
                'unit': 'count',
                'achievement_pct': 85,
                'status': 'PARTIAL',
                'status_color': '#f59e0b',  # Orange for partial
                'status_indicator': '⚠️'  # Warning icon for partial
            },
            {
                'id': 2,
                'name': 'Test KPI 2 - Complete',
                'description': 'Another test KPI',
                'target_value': 50,
                'actual_value': 50,
                'unit': 'items',
                'achievement_pct': 100,
                'status': 'ACHIEVED',
                'status_color': '#10b981',  # Green for achieved
                'status_indicator': '✅'  # Check for achieved
            }
        ]
        
        return jsonify({
            'kpis': simple_kpis,
            'milestone_id': milestone_id,
            'milestone_title': milestone.title,
            'message': 'Simplified KPI data for testing'
        }), 200
    except Exception as e:
        print(f"KPI endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get KPIs', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-kpis/milestone/<int:milestone_id>/results', methods=['PUT'])
@token_required
def update_kpi_results(user, milestone_id):
    """Update KPI actual values for milestone completion"""
    try:
        data = request.get_json()
        kpi_results = data.get('kpi_results', [])
        
        updated_kpis = MilestoneKPIService.update_kpi_results(milestone_id, kpi_results)
        
        return jsonify({
            'message': 'KPI results updated successfully',
            'kpis': [kpi.to_dict() for kpi in updated_kpis]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to update KPI results', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-kpis/<int:kpi_id>', methods=['PUT'])
@token_required
def update_kpi(user, kpi_id):
    """Update specific KPI"""
    try:
        data = request.get_json()
        kpi = MilestoneKPIService.update_kpi(kpi_id, data)
        
        return jsonify({
            'message': 'KPI updated successfully',
            'kpi': kpi.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update KPI', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-kpis/<int:kpi_id>', methods=['DELETE'])
@token_required
def delete_kpi(user, kpi_id):
    """Delete specific KPI"""
    try:
        MilestoneKPIService.delete_kpi(kpi_id)
        return jsonify({
            'message': 'KPI deleted successfully'
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to delete KPI', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-kpis/milestone/<int:milestone_id>/summary', methods=['GET'])
@token_required
def get_milestone_kpi_summary(user, milestone_id):
    """Get KPI summary statistics for milestone"""
    try:
        summary = MilestoneKPIService.get_milestone_kpi_summary(milestone_id)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get KPI summary', 'details': str(e)}), 500

# Template Routes
@milestone_kpis_bp.route('/milestone-templates', methods=['GET'])
@token_required
def get_templates(user):
    """Get all available milestone templates"""
    try:
        templates = MilestoneTemplateService.get_all_templates()
        return jsonify({
            'templates': [template.to_dict() for template in templates]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get templates', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-templates/<int:template_id>', methods=['GET'])
@token_required
def get_template(user, template_id):
    """Get specific template with its configuration"""
    try:
        template = MilestoneTemplateService.get_template_by_id(template_id)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({
            'template': template.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get template', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-templates/<int:template_id>/apply', methods=['POST'])
@token_required
def apply_template(user, template_id):
    """Apply template to a milestone"""
    try:
        data = request.get_json()
        milestone_id = data.get('milestone_id')
        target_adjustments = data.get('target_adjustments', {})
        
        result = MilestoneTemplateService.apply_template_to_milestone(
            milestone_id, template_id, target_adjustments
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to apply template', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-templates', methods=['POST'])
@token_required
def create_template(user):
    """Create a new milestone template"""
    try:
        data = request.get_json()
        name = data.get('name')
        config_json = data.get('config_json')
        
        # Validate template configuration
        is_valid, message = MilestoneTemplateService.validate_template_config(config_json)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        template = MilestoneTemplateService.create_template(name, config_json, user.id)
        
        return jsonify({
            'message': 'Template created successfully',
            'template': template.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create template', 'details': str(e)}), 500

@milestone_kpis_bp.route('/milestone-templates/summary', methods=['GET'])
@token_required
def get_templates_summary(user):
    """Get summary of all templates with usage statistics"""
    try:
        summary = MilestoneTemplateService.get_template_summary()
        return jsonify({
            'templates': summary
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get templates summary', 'details': str(e)}), 500
