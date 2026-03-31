# services/milestone_dashboard_service.py
"""
Milestone Dashboard Service - Phase 3: Reporting
Generates comprehensive dashboards with impact scorecards and operational metrics
"""

from datetime import datetime, timedelta
from models import db, Milestone, MilestoneKPI, AssetAssignment, Task
from services.milestone_kpi_service import MilestoneKPIService
from services.asset_assignment_service import AssetAssignmentService

class MilestoneDashboardService:
    """Service for generating milestone dashboards and reports"""
    
    @staticmethod
    def get_milestone_impact_scorecard(milestone_id):
        """Generate impact scorecard for milestone"""
        from models import Grant
        
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return None
        
        # Get milestone details
        grant = Grant.query.get(milestone.grant_id)
        
        # Get KPIs
        kpis = MilestoneKPIService.get_milestone_kpis(milestone_id)
        
        scorecard = {
            'milestone_info': {
                'id': milestone.id,
                'title': milestone.title,
                'description': milestone.description,
                'status': milestone.status,
                'start_date': milestone.due_date.isoformat() if milestone.due_date else None,  # Use due_date as start
                'end_date': milestone.completion_date.isoformat() if milestone.completion_date else None,  # Use completion_date as end
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
        
        # Process each KPI
        for kpi in kpis:
            kpi_data = {
                'id': kpi.id,
                'name': kpi.name,
                'target': kpi.target_value,
                'actual': kpi.actual_value or 0,
                'unit': kpi.unit,
                'achievement_pct': kpi.achievement_pct or 0,
                'status': kpi.status,
                'evidence_link': kpi.evidence_link
            }
            
            # Add status indicator and color
            if kpi.status == 'ACHIEVED':
                achievement_pct = kpi.achievement_pct or 0
                if achievement_pct >= 120:
                    kpi_data['status_indicator'] = '🟢 Exceptional'
                    kpi_data['status_color'] = '#10b981'
                elif achievement_pct >= 100:
                    kpi_data['status_indicator'] = '🟢 Achieved'
                    kpi_data['status_color'] = '#22c55e'
                else:
                    kpi_data['status_indicator'] = '🟢 Achieved'
                    kpi_data['status_color'] = '#22c55e'
            elif kpi.status == 'PARTIAL':
                kpi_data['status_indicator'] = '🟡 Partial'
                kpi_data['status_color'] = '#f59e0b'
            elif kpi.status == 'PENDING':
                kpi_data['status_indicator'] = '⚪ Pending'
                kpi_data['status_color'] = '#9ca3af'
            else:  # MISSED
                kpi_data['status_indicator'] = '🔴 Missed'
                kpi_data['status_color'] = '#ef4444'
            
            # Add progress bar data
            kpi_data['progress_data'] = {
                'target': kpi.target_value,
                'actual': kpi.actual_value or 0,
                'percentage': min(kpi.achievement_pct or 0, 150)  # Cap at 150% for display
            }
            
            scorecard['kpis'].append(kpi_data)
        
        # Calculate overall metrics
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
        
        return scorecard
    
    @staticmethod
    def get_milestone_operational_metrics(milestone_id):
        """Generate operational efficiency metrics for milestone"""
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return None
        
        # Get asset assignments
        milestone_assets = AssetAssignmentService.get_milestone_assets(milestone_id)
        total_assets = len(milestone_assets)
        returned_assets = len([a for a in milestone_assets if a.status == 'RETURNED'])
        assigned_assets = len([a for a in milestone_assets if a.status == 'ASSIGNED'])
        
        # Calculate utilization metrics
        milestone_duration = 0
        if milestone.due_date and milestone.completion_date:
            milestone_duration = (milestone.completion_date - milestone.due_date).days
        elif milestone.due_date:
            # If no completion date, estimate duration from due date
            milestone_duration = 7  # Default to 7 days
        
        # Asset utilization calculation
        asset_utilization_days = 0
        for assignment in milestone_assets:
            if assignment.assigned_at and (assignment.returned_at or datetime.utcnow()):
                end_date = assignment.returned_at or datetime.utcnow()
                utilization_days = (end_date - assignment.assigned_at).days
                asset_utilization_days += utilization_days
        
        total_possible_utilization = total_assets * milestone_duration
        utilization_rate = (asset_utilization_days / total_possible_utilization * 100) if total_possible_utilization > 0 else 0
        
        # Task productivity
        tasks = Task.query.filter_by(milestone_id=milestone_id).all()
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status.lower() == 'completed'])
        
        # Conflict tracking
        from services.asset_conflict_service import AssetConflictService
        conflicts = AssetConflictService.check_asset_conflicts(
            milestone_id, milestone.due_date, milestone.completion_date
        )
        
        return {
            'milestone_id': milestone_id,
            'milestone_title': milestone.title,
            'asset_integrity': {
                'total_assets': total_assets,
                'assigned_assets': assigned_assets,
                'returned_assets': returned_assets,
                'pending_returns': total_assets - returned_assets,
                'return_rate': (returned_assets / total_assets * 100) if total_assets > 0 else 0,
                'status': '🟢 Complete' if returned_assets == total_assets else '🔴 Incomplete',
                'status_color': '#22c55e' if returned_assets == total_assets else '#ef4444'
            },
            'utilization': {
                'milestone_duration_days': milestone_duration,
                'total_asset_utilization_days': asset_utilization_days,
                'utilization_rate': round(utilization_rate, 1),
                'status': '🟢 Optimal' if utilization_rate >= 80 else '🟡 Moderate' if utilization_rate >= 50 else '🔴 Low',
                'status_color': '#22c55e' if utilization_rate >= 80 else '#f59e0b' if utilization_rate >= 50 else '#ef4444'
            },
            'productivity': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'avg_days_per_task': round(milestone_duration / total_tasks, 1) if total_tasks > 0 else 0,
                'status': '🟢 On Track' if completed_tasks == total_tasks else '🟡 In Progress' if completed_tasks > 0 else '🔴 Not Started',
                'status_color': '#22c55e' if completed_tasks == total_tasks else '#f59e0b' if completed_tasks > 0 else '#ef4444'
            },
            'conflicts': {
                'total_conflicts': len(conflicts),
                'conflicting_assets': len(set([asset for conflict in conflicts for asset in conflict['conflicting_assets']])) if conflicts else 0,
                'status': '🟢 No Conflicts' if len(conflicts) == 0 else '🟡 Some Conflicts' if len(conflicts) <= 3 else '🔴 Many Conflicts',
                'status_color': '#22c55e' if len(conflicts) == 0 else '#f59e0b' if len(conflicts) <= 3 else '#ef4444'
            }
        }
    
    @staticmethod
    def get_grant_dashboard(grant_id):
        """Generate comprehensive dashboard for entire grant"""
        from models import Grant
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return None
        
        # Get all milestones
        milestones = Milestone.query.filter_by(grant_id=grant_id).all()
        
        # Aggregate KPI data
        total_kpis = 0
        total_achieved = 0
        total_partial = 0
        total_missed = 0
        total_pending = 0
        
        # Aggregate asset data
        total_assets_assigned = 0
        total_assets_returned = 0
        
        # Aggregate task data
        total_tasks = 0
        total_completed_tasks = 0
        
        milestone_summaries = []
        
        for milestone in milestones:
            # Get KPI summary
            kpi_summary = MilestoneKPIService.get_milestone_kpi_summary(milestone.id)
            total_kpis += kpi_summary['total_kpis']
            total_achieved += kpi_summary['achieved_kpis']
            total_partial += kpi_summary['partial_kpis']
            total_missed += kpi_summary['missed_kpis']
            total_pending += kpi_summary['pending_kpis']
            
            # Get asset data
            milestone_assets = AssetAssignmentService.get_milestone_assets(milestone.id)
            total_assets_assigned += len(milestone_assets)
            total_assets_returned += len([a for a in milestone_assets if a.status == 'RETURNED'])
            
            # Get task data
            tasks = Task.query.filter_by(milestone_id=milestone.id).all()
            total_tasks += len(tasks)
            total_completed_tasks += len([t for t in tasks if t.status.lower() == 'completed'])
            
            # Create milestone summary
            milestone_summary = {
                'id': milestone.id,
                'title': milestone.title,
                'status': milestone.status,
                'start_date': milestone.start_date.isoformat() if milestone.start_date else None,
                'end_date': milestone.end_date.isoformat() if milestone.end_date else None,
                'kpi_achievement_rate': kpi_summary['overall_achievement'],
                'asset_return_rate': (len([a for a in milestone_assets if a.status == 'RETURNED']) / len(milestone_assets) * 100) if milestone_assets else 100,
                'task_completion_rate': (len([t for t in tasks if t.status.lower() == 'completed']) / len(tasks) * 100) if tasks else 0
            }
            milestone_summaries.append(milestone_summary)
        
        # Calculate grant-level metrics
        overall_kpi_achievement = (total_achieved / total_kpis * 100) if total_kpis > 0 else 0
        overall_asset_return = (total_assets_returned / total_assets_assigned * 100) if total_assets_assigned > 0 else 100
        overall_task_completion = (total_completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'grant_info': {
                'id': grant.id,
                'title': grant.title,
                'grant_code': grant.grant_code,
                'pi_name': grant.pi.name if grant.pi else None,
                'status': grant.status
            },
            'overall_metrics': {
                'total_milestones': len(milestones),
                'completed_milestones': len([m for m in milestones if m.status == 'COMPLETED']),
                'in_progress_milestones': len([m for m in milestones if m.status == 'IN_PROGRESS']),
                'planned_milestones': len([m for m in milestones if m.status == 'PLANNED']),
                'kpi_achievement_rate': round(overall_kpi_achievement, 1),
                'asset_return_rate': round(overall_asset_return, 1),
                'task_completion_rate': round(overall_task_completion, 1)
            },
            'kpi_summary': {
                'total_kpis': total_kpis,
                'achieved': total_achieved,
                'partial': total_partial,
                'missed': total_missed,
                'pending': total_pending
            },
            'asset_summary': {
                'total_assigned': total_assets_assigned,
                'total_returned': total_assets_returned,
                'outstanding': total_assets_assigned - total_assets_returned
            },
            'task_summary': {
                'total_tasks': total_tasks,
                'completed_tasks': total_completed_tasks,
                'pending_tasks': total_tasks - total_completed_tasks
            },
            'milestones': milestone_summaries
        }
    
    @staticmethod
    def generate_performance_trends(grant_id, days_back=90):
        """Generate performance trends for grant over time period"""
        from models import Grant
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return None
        
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get milestones in date range
        milestones = Milestone.query.filter(
            Milestone.grant_id == grant_id,
            Milestone.due_date >= start_date,
            Milestone.due_date <= end_date
        ).order_by(Milestone.due_date).all()
        
        trends = []
        for milestone in milestones:
            # Get KPI achievement for this milestone
            kpi_summary = MilestoneKPIService.get_milestone_kpi_summary(milestone.id)
            
            # Get asset return rate
            milestone_assets = AssetAssignmentService.get_milestone_assets(milestone.id)
            return_rate = (len([a for a in milestone_assets if a.status == 'RETURNED']) / len(milestone_assets) * 100) if milestone_assets else 100
            
            # Get task completion rate
            tasks = Task.query.filter_by(milestone_id=milestone.id).all()
            task_completion = (len([t for t in tasks if t.status.lower() == 'completed']) / len(tasks) * 100) if tasks else 0
            
            trend_data = {
                'milestone_id': milestone.id,
                'milestone_title': milestone.title,
                'completion_date': milestone.completion_date.isoformat() if milestone.completion_date else milestone.due_date.isoformat(),
                'kpi_achievement': kpi_summary['overall_achievement'],
                'asset_return_rate': return_rate,
                'task_completion_rate': task_completion,
                'duration_days': (milestone.completion_date - milestone.due_date).days if milestone.completion_date and milestone.due_date else 7
            }
            trends.append(trend_data)
        
        return {
            'grant_id': grant_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days_back': days_back
            },
            'trends': trends,
            'averages': {
                'avg_kpi_achievement': round(sum([t['kpi_achievement'] for t in trends]) / len(trends), 1) if trends else 0,
                'avg_asset_return_rate': round(sum([t['asset_return_rate'] for t in trends]) / len(trends), 1) if trends else 0,
                'avg_task_completion_rate': round(sum([t['task_completion_rate'] for t in trends]) / len(trends), 1) if trends else 0,
                'avg_duration_days': round(sum([t['duration_days'] for t in trends]) / len(trends), 1) if trends else 0
            }
        }
