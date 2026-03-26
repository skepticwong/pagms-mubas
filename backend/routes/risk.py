# backend/routes/risk.py
from flask import Blueprint, request, jsonify, session
from models import db, Milestone, Grant, User, ComplianceMonitoring
from datetime import datetime, timedelta
import json

risk_bp = Blueprint('risk', __name__)

@risk_bp.route('/api/rsu/risk-heatmap', methods=['GET'])
def get_risk_heatmap():
    """Get institutional risk heatmap data for RSU admins"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get all compliance monitoring records
        records = ComplianceMonitoring.query.all()
        
        heatmap_data = []
        for rec in records:
            heatmap_data.append({
                'grant_id': rec.grant_id,
                'grant_code': rec.grant.grant_code if rec.grant else 'N/A',
                'grant_title': rec.grant.title if rec.grant else 'N/A',
                'overall_score': rec.overall_score,
                'risk_level': rec.risk_level,
                'budget_compliance': rec.budget_compliance_score,
                'reporting_compliance': rec.reporting_compliance_score,
                'task_completion': rec.task_completion_score,
                'last_updated': rec.updated_at.isoformat()
            })
            
        return jsonify({
            'heatmap': heatmap_data,
            'summary': {
                'total_grants': len(heatmap_data),
                'risk_counts': {
                    'critical': len([r for r in heatmap_data if r['risk_level'] == 'critical']),
                    'high': len([r for r in heatmap_data if r['risk_level'] == 'high']),
                    'medium': len([r for r in heatmap_data if r['risk_level'] == 'medium']),
                    'low': len([r for r in heatmap_data if r['risk_level'] == 'low'])
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@risk_bp.route('/api/rsu/waiver-analytics', methods=['GET'])
def get_waiver_analytics():
    """Get statistics on effort certification waivers"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Query milestones with waivers
        waivers = Milestone.query.filter(
            db.or_(
                Milestone.waiver_requested == True,
                Milestone.waiver_approved == True
            )
        ).all()
        
        analytics = {
            'total_requests': len(waivers),
            'approved_count': len([w for w in waivers if w.waiver_approved]),
            'pending_count': len([w for w in waivers if w.waiver_requested and not w.waiver_approved]),
            'reasons_breakdown': {},
            'grant_distribution': {}
        }
        
        for w in waivers:
            # Breakdown by reason
            reason = w.waiver_reason or 'Not Specified'
            analytics['reasons_breakdown'][reason] = analytics['reasons_breakdown'].get(reason, 0) + 1
            
            # Distribution by grant
            grant_code = w.grant.grant_code if w.grant else 'Unknown'
            analytics['grant_distribution'][grant_code] = analytics['grant_distribution'].get(grant_code, 0) + 1
            
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
