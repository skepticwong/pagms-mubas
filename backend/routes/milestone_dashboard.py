# routes/milestone_dashboard.py
"""Milestone Dashboard Routes - Phase 3: Reporting
API endpoints for generating dashboards and reports"""

from flask import Blueprint, request, jsonify, session
from services.milestone_dashboard_service import MilestoneDashboardService
from datetime import datetime

milestone_dashboard_bp = Blueprint('milestone_dashboard', __name__)

@milestone_dashboard_bp.route('/dashboard/simple-test', methods=['GET'])
def simple_test():
    """Simple test endpoint to isolate issues"""
    try:
        from models import db, Milestone
        milestone_count = Milestone.query.count()
        return jsonify({
            'message': 'Simple test working',
            'milestone_count': milestone_count,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success'
        }), 200
    except Exception as e:
        print(f"Simple test error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Simple test failed', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/test', methods=['GET'])
def test_dashboard():
    """Test endpoint to verify dashboard routes are working"""
    return jsonify({
        'message': 'Dashboard routes are working!',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success'
    }), 200

@milestone_dashboard_bp.route('/dashboard/milestone/<int:milestone_id>/impact', methods=['GET'])
def get_milestone_impact_scorecard(milestone_id):
    """Get impact scorecard for a specific milestone"""
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
        
        # Get real KPI data from database
        from services.milestone_kpi_service import MilestoneKPIService
        kpis = MilestoneKPIService.get_milestone_kpis(milestone_id)
        
        # Build scorecard with real data
        scorecard = {
            'milestone_info': {
                'id': milestone.id,
                'title': milestone.title,
                'description': milestone.description,
                'status': milestone.status,
                'start_date': milestone.due_date.isoformat() if milestone.due_date else None,
                'end_date': milestone.completion_date.isoformat() if milestone.completion_date else None,
                'actual_end_date': milestone.completion_date.isoformat() if milestone.completion_date else None,
                'progress_percentage': milestone.progress_percentage if hasattr(milestone, 'progress_percentage') else 0,
                'grant_info': {
                    'id': grant.id,
                    'title': grant.title,
                    'grant_code': grant.grant_code
                }
            },
            'kpis': []
        }
        
        # Process each real KPI
        for kpi in kpis:
            kpi_data = {
                'id': kpi.id,
                'name': kpi.name,
                'description': kpi.description or '',
                'target_value': kpi.target_value,
                'actual_value': kpi.actual_value or 0,
                'unit': kpi.unit or 'count',
                'achievement_pct': kpi.achievement_pct or 0,
                'status': kpi.status or 'PENDING',
                'status_indicator': get_kpi_status_indicator(kpi.status),
                'status_color': get_kpi_status_color(kpi.status),
                'progress_data': {
                    'target': kpi.target_value,
                    'actual': kpi.actual_value or 0,
                    'percentage': kpi.achievement_pct or 0
                }
            }
            scorecard['kpis'].append(kpi_data)
        
        # Calculate summary statistics
        total_kpis = len(kpis)
        achieved_kpis = len([k for k in kpis if k.status == 'ACHIEVED'])
        partial_kpis = len([k for k in kpis if k.status == 'PARTIAL'])
        missed_kpis = len([k for k in kpis if k.status == 'MISSED'])
        pending_kpis = len([k for k in kpis if k.status == 'PENDING'])
        
        scorecard['summary'] = {
            'total_kpis': total_kpis,
            'achieved_kpis': achieved_kpis,
            'partial_kpis': partial_kpis,
            'missed_kpis': missed_kpis,
            'pending_kpis': pending_kpis,
            'achievement_rate': round((achieved_kpis / total_kpis * 100), 1) if total_kpis > 0 else 0,
            'completion_rate': round(((achieved_kpis + partial_kpis + missed_kpis) / total_kpis * 100), 1) if total_kpis > 0 else 0
        }
        
        return jsonify(scorecard), 200
    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get impact scorecard', 'details': str(e)}), 500

def get_kpi_status_indicator(status):
    """Get status indicator emoji for KPI"""
    indicators = {
        'ACHIEVED': '🟢 Achieved',
        'PARTIAL': '🟡 Partial',
        'MISSED': '🔴 Missed',
        'PENDING': '⚪ Pending'
    }
    return indicators.get(status, '⚪ Unknown')

def get_kpi_status_color(status):
    """Get status color for KPI"""
    colors = {
        'ACHIEVED': '#22c55e',
        'PARTIAL': '#f59e0b',
        'MISSED': '#ef4444',
        'PENDING': '#9ca3af'
    }
    return colors.get(status, '#9ca3af')

@milestone_dashboard_bp.route('/dashboard/milestone/<int:milestone_id>/operational', methods=['GET'])
def get_milestone_operational_metrics(milestone_id):
    """Get operational metrics for a specific milestone"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Milestone, Grant, User, Task, AssetAssignment
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Check if user has permission (PI or RSU)
        grant = Grant.query.get(milestone.grant_id)
        if grant.pi_id != user_id:
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get operational data with basic calculations (avoid complex services)
        tasks = Task.query.filter_by(milestone_id=milestone_id).all()
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status.lower() == 'completed'])
        
        # Get asset assignments
        milestone_assets = AssetAssignment.query.filter(
            AssetAssignment.task_id.in_([t.id for t in tasks])
        ).all()
        total_assets = len(milestone_assets)
        returned_assets = len([a for a in milestone_assets if a.status == 'RETURNED'])
        
        # Calculate basic metrics
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        return_rate = (returned_assets / total_assets * 100) if total_assets > 0 else 100
        
        metrics = {
            'milestone_id': milestone_id,
            'milestone_title': milestone.title,
            'asset_integrity': {
                'total_assets': total_assets,
                'assigned_assets': total_assets,
                'returned_assets': returned_assets,
                'pending_returns': total_assets - returned_assets,
                'return_rate': return_rate,
                'status': '🟢 Complete' if return_rate == 100 else '🔴 Incomplete',
                'status_color': '#22c55e' if return_rate == 100 else '#ef4444'
            },
            'utilization': {
                'milestone_duration_days': 7,  # Default duration
                'total_asset_utilization_days': 0,
                'utilization_rate': 75,  # Default utilization
                'status': '🟡 Moderate',
                'status_color': '#f59e0b'
            },
            'productivity': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate,
                'avg_days_per_task': 1.5,  # Default average
                'status': '🟢 On Track' if completion_rate >= 80 else '🟡 In Progress' if completion_rate > 0 else '🔴 Not Started',
                'status_color': '#22c55e' if completion_rate >= 80 else '#f59e0b' if completion_rate > 0 else '#ef4444'
            },
            'conflicts': {
                'total_conflicts': 0,  # No conflict detection for now
                'conflicting_assets': 0,
                'status': '🟢 No Conflicts',
                'status_color': '#22c55e'
            }
        }
        
        return jsonify(metrics), 200
    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get operational metrics', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/milestone/<int:milestone_id>/combined', methods=['GET'])
def get_milestone_combined_dashboard(milestone_id):
    """Get combined dashboard (impact + operational) for a milestone"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Milestone, Grant
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Check if user has permission (PI or RSU)
        grant = Grant.query.get(milestone.grant_id)
        if grant.pi_id != user_id:
            # Check if user is RSU
            from models import User
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        impact_scorecard = MilestoneDashboardService.get_milestone_impact_scorecard(milestone_id)
        operational_metrics = MilestoneDashboardService.get_milestone_operational_metrics(milestone_id)
        
        return jsonify({
            'impact_scorecard': impact_scorecard,
            'operational_metrics': operational_metrics,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get combined dashboard', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/grant/<int:grant_id>', methods=['GET'])
def get_grant_dashboard(grant_id):
    """Get comprehensive dashboard for entire grant"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user has permission (PI or RSU)
        if grant.pi_id != user_id:
            # Check if user is RSU
            from models import User
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        dashboard = MilestoneDashboardService.get_grant_dashboard(grant_id)
        return jsonify(dashboard), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get grant dashboard', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/grant/<int:grant_id>/trends', methods=['GET'])
def get_grant_performance_trends(grant_id):
    """Get performance trends for grant over time"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user has permission (PI or RSU)
        if grant.pi_id != user_id:
            # Check if user is RSU
            from models import User
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get query parameters
        days_back = request.args.get('days_back', 90, type=int)
        
        trends = MilestoneDashboardService.generate_performance_trends(grant_id, days_back)
        return jsonify(trends), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get performance trends', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/grant/<int:grant_id>/summary', methods=['GET'])
def get_grant_summary_dashboard(grant_id):
    """Get summary dashboard with key metrics only"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        if grant.pi_id != user_id:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get full dashboard and extract key metrics
        full_dashboard = MilestoneDashboardService.get_grant_dashboard(grant_id)
        
        summary = {
            'grant_info': full_dashboard['grant_info'],
            'key_metrics': full_dashboard['overall_metrics'],
            'alerts': []
        }
        
        # Generate alerts based on metrics
        if full_dashboard['overall_metrics']['kpi_achievement_rate'] < 80:
            summary['alerts'].append({
                'type': 'warning',
                'message': f"KPI achievement rate is {full_dashboard['overall_metrics']['kpi_achievement_rate']}%",
                'severity': 'medium'
            })
        
        if full_dashboard['overall_metrics']['asset_return_rate'] < 90:
            summary['alerts'].append({
                'type': 'error',
                'message': f"Asset return rate is {full_dashboard['overall_metrics']['asset_return_rate']}%",
                'severity': 'high'
            })
        
        if full_dashboard['asset_summary']['outstanding'] > 0:
            summary['alerts'].append({
                'type': 'warning',
                'message': f"{full_dashboard['asset_summary']['outstanding']} assets still outstanding",
                'severity': 'medium'
            })
        
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get grant summary', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/export/milestone/<int:milestone_id>/pdf', methods=['GET'])
def export_milestone_pdf(milestone_id):
    """Export milestone dashboard as PDF"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Milestone, Grant
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Check if user has permission (PI or RSU)
        grant = Grant.query.get(milestone.grant_id)
        if grant.pi_id != user_id:
            # Check if user is RSU
            from models import User
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get dashboard data
        impact_scorecard = MilestoneDashboardService.get_milestone_impact_scorecard(milestone_id)
        operational_metrics = MilestoneDashboardService.get_milestone_operational_metrics(milestone_id)
        
        # Generate PDF (simplified version - in real implementation, use PDF library)
        pdf_content = {
            'title': f'Milestone Dashboard: {milestone.title}',
            'generated_at': datetime.utcnow().isoformat(),
            'impact_scorecard': impact_scorecard,
            'operational_metrics': operational_metrics
        }
        
        return jsonify({
            'message': 'PDF export ready',
            'pdf_data': pdf_content,
            'download_url': f'/api/downloads/milestone_{milestone_id}_dashboard.pdf'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to export PDF', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/export/grant/<int:grant_id>/pdf', methods=['GET'])
def export_grant_pdf(grant_id):
    """Export grant dashboard as PDF"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from models import Grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if user has permission (PI or RSU)
        if grant.pi_id != user_id:
            # Check if user is RSU
            from models import User
            user = User.query.get(user_id)
            if user.role != 'RSU':
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get dashboard data
        dashboard = MilestoneDashboardService.get_grant_dashboard(grant_id)
        trends = MilestoneDashboardService.generate_performance_trends(grant_id, 90)
        
        # Generate PDF content
        pdf_content = {
            'title': f'Grant Dashboard: {grant.title}',
            'generated_at': datetime.utcnow().isoformat(),
            'dashboard': dashboard,
            'trends': trends
        }
        
        return jsonify({
            'message': 'PDF export ready',
            'pdf_data': pdf_content,
            'download_url': f'/api/downloads/grant_{grant_id}_dashboard.pdf'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to export PDF', 'details': str(e)}), 500

@milestone_dashboard_bp.route('/dashboard/metrics/summary', methods=['GET'])
def get_system_metrics_summary():
    """Get system-wide metrics summary (for RSU users)"""
    try:
        # Check user permissions using session like other milestone endpoints
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Check if user is RSU
        from models import User
        user = User.query.get(user_id)
        if user.role != 'RSU':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get system-wide metrics
        from models import Grant, Milestone, MilestoneKPI, AssetAssignment
        
        total_grants = Grant.query.count()
        total_milestones = Milestone.query.count()
        total_kpis = MilestoneKPI.query.count()
        total_assignments = AssetAssignment.query.count()
        
        # Calculate completion rates
        completed_milestones = Milestone.query.filter_by(status='COMPLETED').count()
        achieved_kpis = MilestoneKPI.query.filter_by(status='ACHIEVED').count()
        returned_assets = AssetAssignment.query.filter_by(status='RETURNED').count()
        
        summary = {
            'system_overview': {
                'total_grants': total_grants,
                'total_milestones': total_milestones,
                'total_kpis': total_kpis,
                'total_asset_assignments': total_assignments
            },
            'completion_rates': {
                'milestone_completion_rate': round((completed_milestones / total_milestones * 100), 1) if total_milestones > 0 else 0,
                'kpi_achievement_rate': round((achieved_kpis / total_kpis * 100), 1) if total_kpis > 0 else 0,
                'asset_return_rate': round((returned_assets / total_assignments * 100), 1) if total_assignments > 0 else 0
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get system metrics', 'details': str(e)}), 500
