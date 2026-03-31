"""
Asset Audit Routes - Audit trail and compliance monitoring endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from middleware.auth import token_required
from services.asset_audit_service import AssetAuditService
from models import Asset, User
from typing import Dict, List
import io
import json

audit_bp = Blueprint('asset_audit', __name__)

@audit_bp.route('/assets/<int:asset_id>/audit-log', methods=['POST'])
@token_required
def create_audit_log(user, asset_id):
    """Create audit log entry for asset activity"""
    try:
        data = request.get_json()
        
        action = data.get('action')
        details = data.get('details', {})
        ip_address = request.remote_addr
        
        # Add request context to details
        details['user_agent'] = request.headers.get('User-Agent', '')
        details['session_id'] = request.cookies.get('session_id', '')
        
        audit_log = AssetAuditService.create_audit_log(asset_id, action, details, user.id, ip_address)
        
        return jsonify({
            'message': 'Audit log created successfully',
            'audit_log': audit_log
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create audit log'}), 500

@audit_bp.route('/assets/<int:asset_id>/audit-trail', methods=['GET'])
@token_required
def get_asset_audit_trail(user, asset_id):
    """Get audit trail for a specific asset"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        audit_trail = AssetAuditService.get_asset_audit_trail(asset_id, start_date, end_date)
        
        return jsonify({
            'audit_trail': audit_trail,
            'total': len(audit_trail)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch audit trail'}), 500

@audit_bp.route('/assets/grant/<int:grant_id>/audit-trail', methods=['GET'])
@token_required
def get_grant_audit_trail(user, grant_id):
    """Get audit trail for all assets in a grant"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        action_filter = request.args.get('action_filter')
        
        audit_trail = AssetAuditService.get_grant_audit_trail(grant_id, start_date, end_date, action_filter)
        
        return jsonify({
            'audit_trail': audit_trail,
            'total': len(audit_trail)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch grant audit trail'}), 500

@audit_bp.route('/assets/user/<int:user_id>/audit-activity', methods=['GET'])
@token_required
def get_user_audit_activity(user, user_id):
    """Get audit activity for a specific user"""
    try:
        # Only allow users to view their own activity or admins to view any user
        if user.id != user_id and user.role not in ['RSU', 'Finance']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        user_activities = AssetAuditService.get_user_audit_activity(user_id, start_date, end_date)
        
        return jsonify({
            'user_activities': user_activities,
            'total': len(user_activities)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch user audit activity'}), 500

@audit_bp.route('/assets/grant/<int:grant_id>/audit-report', methods=['GET'])
@token_required
def generate_audit_report(user, grant_id):
    """Generate comprehensive audit report"""
    try:
        report_type = request.args.get('report_type', 'comprehensive')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        report = AssetAuditService.generate_audit_report(grant_id, report_type, start_date, end_date)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate audit report'}), 500

@audit_bp.route('/assets/grant/<int:grant_id>/audit-statistics', methods=['GET'])
@token_required
def get_audit_statistics(user, grant_id):
    """Get audit statistics for recent activity"""
    try:
        days = request.args.get('days', 30, type=int)
        
        stats = AssetAuditService.get_audit_statistics(grant_id, days)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch audit statistics'}), 500

@audit_bp.route('/assets/grant/<int:grant_id>/audit-anomalies', methods=['GET'])
@token_required
def detect_audit_anomalies(user, grant_id):
    """Detect anomalous activities in audit trail"""
    try:
        days = request.args.get('days', 30, type=int)
        
        anomalies = AssetAuditService.detect_anomalies(grant_id, days)
        
        return jsonify({
            'anomalies': anomalies,
            'total': len(anomalies)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to detect anomalies'}), 500

@audit_bp.route('/assets/grant/<int:grant_id>/audit-export', methods=['GET'])
@token_required
def export_audit_trail(user, grant_id):
    """Export audit trail in specified format"""
    try:
        format_type = request.args.get('format', 'json')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        export_data = AssetAuditService.export_audit_trail(grant_id, format_type, start_date, end_date)
        
        if format_type in ['csv', 'excel']:
            return send_file(
                io.BytesIO(export_data['content'].encode()),
                as_attachment=True,
                download_name=export_data['filename'],
                mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(export_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to export audit trail'}), 500

@audit_bp.route('/assets/audit-actions', methods=['GET'])
@token_required
def get_audit_actions(user):
    """Get available audit action types"""
    try:
        actions = [
            'asset_created',
            'asset_updated',
            'asset_disposed',
            'asset_transferred',
            'asset_status_changed',
            'custodian_changed',
            'maintenance_completed',
            'maintenance_scheduled',
            'document_uploaded',
            'document_updated',
            'document_deleted',
            'transfer_requested',
            'transfer_approved',
            'transfer_rejected',
            'alert_dismissed',
            'high_value_modification',
            'compliance_flagged'
        ]
        
        return jsonify({'actions': actions}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch audit actions'}), 500

@audit_bp.route('/assets/audit-impact-levels', methods=['GET'])
@token_required
def get_impact_levels(user):
    """Get available impact levels"""
    try:
        levels = [
            {'value': 'low', 'description': 'Routine activities with minimal impact'},
            {'value': 'medium', 'description': 'Moderate impact activities requiring attention'},
            {'value': 'high', 'description': 'High impact activities requiring review'}
        ]
        
        return jsonify({'impact_levels': levels}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch impact levels'}), 500

@audit_bp.route('/assets/grant/<int:grant_id>/audit-summary', methods=['GET'])
@token_required
def get_audit_summary(user, grant_id):
    """Get quick audit summary for dashboard"""
    try:
        days = request.args.get('days', 7, type=int)
        
        stats = AssetAuditService.get_audit_statistics(grant_id, days)
        anomalies = AssetAuditService.detect_anomalies(grant_id, days)
        
        summary = {
            'period_days': days,
            'total_activities': stats['total_activities'],
            'unique_users': stats['unique_users'],
            'high_impact_activities': stats['high_impact_activities'],
            'compliance_flags': stats['compliance_flags'],
            'anomalies_count': len(anomalies),
            'recent_activities': stats['activities_by_day'],
            'top_actions': stats['top_actions'][:5]
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch audit summary'}), 500

@audit_bp.route('/assets/audit-compliance/<int:grant_id>', methods=['GET'])
@token_required
def get_compliance_audit(user, grant_id):
    """Get compliance-focused audit information"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        audit_trail = AssetAuditService.get_grant_audit_trail(grant_id, start_date, end_date)
        
        # Filter for compliance-flagged activities
        compliance_activities = [
            entry for entry in audit_trail 
            if entry.get('compliance_flag') or entry.get('impact_level') == 'high'
        ]
        
        # Group by compliance type
        compliance_by_type = {}
        for activity in compliance_activities:
            compliance_type = activity.get('action', 'unknown')
            if compliance_type not in compliance_by_type:
                compliance_by_type[compliance_type] = []
            compliance_by_type[compliance_type].append(activity)
        
        # Get user compliance statistics
        user_compliance = {}
        for activity in compliance_activities:
            user_id = activity['user_id']
            if user_id not in user_compliance:
                user_compliance[user_id] = 0
            user_compliance[user_id] += 1
        
        return jsonify({
            'compliance_activities': compliance_activities,
            'compliance_by_type': compliance_by_type,
            'user_compliance': user_compliance,
            'total_compliance_flags': len(compliance_activities)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch compliance audit'}), 500

@audit_bp.route('/assets/audit-activity-patterns/<int:grant_id>', methods=['GET'])
@token_required
def get_activity_patterns(user, grant_id):
    """Get activity patterns and trends"""
    try:
        days = request.args.get('days', 30, type=int)
        
        stats = AssetAuditService.get_audit_statistics(grant_id, days)
        
        # Analyze patterns
        patterns = {
            'daily_distribution': stats['activities_by_day'],
            'peak_activity_days': AssetAuditService._get_peak_activity_days(stats['activities_by_day']),
            'user_activity_distribution': stats['most_active_users'],
            'asset_activity_distribution': stats['most_active_assets'],
            'action_frequency': stats['top_actions']
        }
        
        return jsonify(patterns), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch activity patterns'}), 500

# Helper function for peak activity days
@staticmethod
def _get_peak_activity_days(activities_by_day):
    """Get days with highest activity"""
    if not activities_by_day:
        return []
    
    sorted_days = sorted(activities_by_day.items(), key=lambda x: x[1], reverse=True)
    return sorted_days[:5]  # Top 5 peak days

# Auto-create audit logs for asset activities (this would be integrated into other services)
@audit_bp.route('/assets/auto-audit', methods=['POST'])
@token_required
def auto_create_audit_log(user):
    """Auto-create audit log for asset activities (internal use)"""
    try:
        data = request.get_json()
        
        asset_id = data.get('asset_id')
        action = data.get('action')
        details = data.get('details', {})
        
        if not asset_id or not action:
            return jsonify({'error': 'Asset ID and action are required'}), 400
        
        # Auto-populate some details
        details['auto_generated'] = True
        details['source'] = 'asset_service'
        
        audit_log = AssetAuditService.create_audit_log(asset_id, action, details, user.id, request.remote_addr)
        
        return jsonify({
            'message': 'Auto audit log created',
            'audit_log': audit_log
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create auto audit log'}), 500
