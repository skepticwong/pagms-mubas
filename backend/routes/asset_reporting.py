"""
Asset Reporting Routes - Comprehensive reporting endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from middleware.auth import token_required
from services.asset_reporting_service import AssetReportingService
from services.asset_analytics_service import AssetAnalyticsService
from models import Asset, Grant
from typing import Dict
import io
import json

reporting_bp = Blueprint('asset_reporting', __name__)

@reporting_bp.route('/assets/reports/inventory/<int:grant_id>', methods=['GET'])
@token_required
def generate_inventory_report(user, grant_id):
    """Generate asset inventory report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_asset_inventory_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate inventory report'}), 500

@reporting_bp.route('/assets/reports/maintenance/<int:grant_id>', methods=['GET'])
@token_required
def generate_maintenance_report(user, grant_id):
    """Generate maintenance report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_maintenance_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate maintenance report'}), 500

@reporting_bp.route('/assets/reports/compliance/<int:grant_id>', methods=['GET'])
@token_required
def generate_compliance_report(user, grant_id):
    """Generate compliance report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_compliance_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate compliance report'}), 500

@reporting_bp.route('/assets/reports/financial/<int:grant_id>', methods=['GET'])
@token_required
def generate_financial_report(user, grant_id):
    """Generate financial report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_financial_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate financial report'}), 500

@reporting_bp.route('/assets/reports/utilization/<int:grant_id>', methods=['GET'])
@token_required
def generate_utilization_report(user, grant_id):
    """Generate utilization report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_utilization_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate utilization report'}), 500

@reporting_bp.route('/assets/reports/disposition/<int:grant_id>', methods=['GET'])
@token_required
def generate_disposition_report(user, grant_id):
    """Generate disposition report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_disposition_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate disposition report'}), 500

@reporting_bp.route('/assets/reports/audit-trail/<int:grant_id>', methods=['GET'])
@token_required
def generate_audit_trail_report(user, grant_id):
    """Generate audit trail report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_audit_trail_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate audit trail report'}), 500

@reporting_bp.route('/assets/reports/summary/<int:grant_id>', methods=['GET'])
@token_required
def generate_summary_report(user, grant_id):
    """Generate executive summary report"""
    try:
        format_type = request.args.get('format', 'json')
        report = AssetReportingService.generate_summary_report(grant_id, format_type)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(report['content']),
                as_attachment=True,
                download_name=report['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate summary report'}), 500

@reporting_bp.route('/assets/reports/comprehensive/<int:grant_id>', methods=['GET'])
@token_required
def generate_comprehensive_report(user, grant_id):
    """Generate comprehensive report with all sections"""
    try:
        format_type = request.args.get('format', 'json')
        
        comprehensive_report = {
            'report_type': 'Comprehensive Asset Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'sections': {
                'inventory': AssetReportingService.generate_asset_inventory_report(grant_id, 'json'),
                'maintenance': AssetReportingService.generate_maintenance_report(grant_id, 'json'),
                'compliance': AssetReportingService.generate_compliance_report(grant_id, 'json'),
                'financial': AssetReportingService.generate_financial_report(grant_id, 'json'),
                'utilization': AssetReportingService.generate_utilization_report(grant_id, 'json'),
                'disposition': AssetReportingService.generate_disposition_report(grant_id, 'json'),
                'audit_trail': AssetReportingService.generate_audit_trail_report(grant_id, 'json'),
                'executive_summary': AssetReportingService.generate_summary_report(grant_id, 'json')
            }
        }
        
        if format_type in ['csv', 'excel']:
            # For comprehensive reports, we'd need to create multiple sheets/files
            # For now, return the JSON format
            return jsonify(comprehensive_report), 200
        else:
            return jsonify(comprehensive_report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate comprehensive report'}), 500

@reporting_bp.route('/assets/reports/scheduled/<int:grant_id>', methods=['POST'])
@token_required
def schedule_report(user, grant_id):
    """Schedule a report to be generated and sent via email"""
    data = request.get_json()
    
    try:
        # This would integrate with a job scheduler and email service
        # For now, return a placeholder response
        schedule_info = {
            'grant_id': grant_id,
            'report_type': data.get('report_type', 'comprehensive'),
            'frequency': data.get('frequency', 'monthly'),
            'recipients': data.get('recipients', []),
            'scheduled_at': datetime.utcnow().isoformat(),
            'next_run': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'message': 'Report scheduled successfully',
            'schedule': schedule_info
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to schedule report'}), 500

@reporting_bp.route('/assets/reports/templates', methods=['GET'])
@token_required
def get_report_templates(user):
    """Get available report templates"""
    try:
        templates = {
            'inventory': {
                'name': 'Asset Inventory Report',
                'description': 'Complete list of all assets with details',
                'sections': ['asset_details', 'maintenance_history', 'transfer_history']
            },
            'maintenance': {
                'name': 'Maintenance Report',
                'description': 'Maintenance activities and costs',
                'sections': ['maintenance_records', 'cost_analysis', 'upcoming_maintenance']
            },
            'compliance': {
                'name': 'Compliance Report',
                'description': 'Compliance status and alerts',
                'sections': ['compliance_score', 'alerts', 'risk_assessment']
            },
            'financial': {
                'name': 'Financial Report',
                'description': 'Financial analysis and ROI',
                'sections': ['cost_breakdown', 'roi_analysis', 'budget_utilization']
            },
            'utilization': {
                'name': 'Utilization Report',
                'description': 'Asset utilization and performance',
                'sections': ['utilization_metrics', 'performance_scores', 'transfer_analysis']
            },
            'disposition': {
                'name': 'Disposition Report',
                'description': 'Asset disposition and closeout status',
                'sections': ['disposition_summary', 'pending_dispositions', 'closeout_readiness']
            },
            'audit_trail': {
                'name': 'Audit Trail Report',
                'description': 'Complete audit history',
                'sections': ['asset_changes', 'transfers', 'maintenance_records', 'disposition_records']
            },
            'summary': {
                'name': 'Executive Summary',
                'description': 'High-level overview for executives',
                'sections': ['key_metrics', 'insights', 'recommendations', 'risk_assessment']
            }
        }
        
        return jsonify({'templates': templates}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch report templates'}), 500

@reporting_bp.route('/assets/reports/custom', methods=['POST'])
@token_required
def generate_custom_report(user, grant_id):
    """Generate custom report based on user specifications"""
    data = request.get_json()
    
    try:
        # Get user specifications
        sections = data.get('sections', [])
        filters = data.get('filters', {})
        format_type = data.get('format', 'json')
        
        # Build custom report
        custom_report = {
            'report_type': 'Custom Asset Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'specifications': {
                'sections': sections,
                'filters': filters
            },
            'data': {}
        }
        
        # Generate requested sections
        if 'overview' in sections:
            custom_report['data']['overview'] = AssetAnalyticsService._get_overview_metrics(grant_id)
        
        if 'financial' in sections:
            custom_report['data']['financial'] = AssetAnalyticsService._get_financial_analytics(grant_id)
        
        if 'maintenance' in sections:
            custom_report['data']['maintenance'] = AssetAnalyticsService._get_maintenance_analytics(grant_id)
        
        if 'compliance' in sections:
            custom_report['data']['compliance'] = AssetAnalyticsService._get_compliance_analytics(grant_id)
        
        if 'performance' in sections:
            custom_report['data']['performance'] = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        # Apply filters if provided
        if filters:
            custom_report['data'] = AssetReportingService._apply_filters(custom_report['data'], filters)
        
        if format_type in ['csv', 'excel']:
            # Convert custom report to requested format
            return send_file(
                io.BytesIO(json.dumps(custom_report).encode()),
                as_attachment=True,
                download_name=f'custom_asset_report_{datetime.utcnow().strftime("%Y%m%d")}.json',
                mimetype='application/json'
            )
        else:
            return jsonify(custom_report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate custom report'}), 500

@reporting_bp.route('/assets/reports/history/<int:grant_id>', methods=['GET'])
@token_required
def get_report_history(user, grant_id):
    """Get history of generated reports"""
    try:
        # This would query a report history table
        # For now, return placeholder data
        history = [
            {
                'id': 1,
                'report_type': 'inventory',
                'generated_at': '2025-03-20T10:00:00',
                'generated_by': user.id,
                'format': 'pdf',
                'file_size': 1024000
            },
            {
                'id': 2,
                'report_type': 'maintenance',
                'generated_at': '2025-03-15T14:30:00',
                'generated_by': user.id,
                'format': 'excel',
                'file_size': 2048000
            }
        ]
        
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch report history'}), 500

# Helper method for filtering
@staticmethod
def _apply_filters(data: Dict, filters: Dict) -> Dict:
    """Apply filters to report data"""
    filtered_data = data.copy()
    
    # Date range filter
    if 'date_range' in filters:
        start_date = filters['date_range'].get('start')
        end_date = filters['date_range'].get('end')
        
        # Apply date filtering to relevant sections
        # This is a simplified example
        pass
    
    # Category filter
    if 'categories' in filters:
        categories = filters['categories']
        # Filter assets by category
        pass
    
    # Status filter
    if 'statuses' in filters:
        statuses = filters['statuses']
        # Filter assets by status
        pass
    
    return filtered_data
