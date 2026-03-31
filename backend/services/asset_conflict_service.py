# services/asset_conflict_service.py
"""
Asset Conflict Detection Service - Phase 2: Planning Core
Prevents resource conflicts during milestone planning
"""

from datetime import datetime, timedelta
from models import db, Milestone, Task, AssetAssignment, Asset

class AssetConflictService:
    """Service for detecting and managing asset conflicts"""
    
    @staticmethod
    def check_asset_conflicts(milestone_id, start_date, end_date):
        """Check for asset conflicts during milestone period"""
        conflicts = []
        
        # Get all asset assignments for this milestone
        milestone_assets = AssetAssignmentService.get_milestone_assets(milestone_id)
        
        # Get all other assignments in the same period
        all_assignments = AssetAssignment.query.filter(
            AssetAssignment.assigned_at <= end_date,
            (AssetAssignment.returned_at >= start_date) | (AssetAssignment.returned_at.is_(None))
        ).all()
        
        # Check for conflicts
        for assignment in milestone_assets:
            conflicting_assignments = [
                a for a in all_assignments 
                if a.asset_id == assignment.asset_id and 
                a.id != assignment.id and
                not (a.returned_at and a.returned_at <= start_date)
            ]
            
            if conflicting_assignments:
                conflicts.append({
                    'asset_id': assignment.asset_id,
                    'asset_name': assignment.asset.name if assignment.asset else f'Asset {assignment.asset_id}',
                    'conflict_type': 'double_booking',
                    'conflicting_assignments': [
                        {
                            'assignment_id': a.id,
                            'assigned_to': a.assigned_to.name if a.assigned_to else f'User {a.assigned_to}',
                            'period': f'{a.assigned_at} to {a.returned_at or "ongoing"}'
                        } for a in conflicting_assignments
                    ],
                    'suggested_resolution': 'reschedule_one_assignment',
                    'severity': 'high' if len(conflicting_assignments) > 1 else 'medium'
                })
        
        return conflicts
    
    @staticmethod
    def _get_milestone_assets(milestone_id):
        """Get all asset assignments for a milestone"""
        tasks = Task.query.filter_by(milestone_id=milestone_id).all()
        all_assignments = []
        
        for task in tasks:
            assignments = AssetAssignment.query.filter_by(task_id=task.id).all()
            all_assignments.extend(assignments)
        
        return all_assignments
    
    @staticmethod
    def check_asset_availability(asset_id, start_date, end_date):
        """Check if specific asset is available during time period"""
        # Get all active assignments for this asset during the period
        conflicting_assignments = db.session.query(AssetAssignment).join(Task).join(Milestone).filter(
            AssetAssignment.asset_id == asset_id,
            AssetAssignment.status.in_(['REQUESTED', 'ASSIGNED']),
            Milestone.due_date <= end_date,
            Milestone.completion_date >= start_date,
            Milestone.status.in_(['IN_PROGRESS', 'PLANNED'])
        ).all()
        
        return len(conflicting_assignments) == 0
    
    @staticmethod
    def get_asset_utilization_schedule(asset_id, start_date, end_date):
        """Get detailed utilization schedule for an asset"""
        assignments = db.session.query(AssetAssignment).join(Task).join(Milestone).filter(
            AssetAssignment.asset_id == asset_id,
            Milestone.start_date <= end_date,
            Milestone.end_date >= start_date,
            Milestone.status.in_(['IN_PROGRESS', 'PLANNED', 'COMPLETED'])
        ).order_by(Milestone.start_date).all()
        
        schedule = []
        for assignment in assignments:
            schedule.append({
                'milestone_id': assignment.task.milestone.id,
                'milestone_title': assignment.task.milestone.title,
                'task_id': assignment.task.id,
                'task_title': assignment.task.title,
                'assigned_to': assignment.assigned_user.name if assignment.assigned_user else 'Unassigned',
                'status': assignment.status,
                'period': {
                    'start': assignment.task.milestone.start_date.isoformat(),
                    'end': assignment.task.milestone.end_date.isoformat()
                }
            })
        
        return schedule
    
    @staticmethod
    def get_conflict_resolution_suggestions(conflicts):
        """Suggest resolutions for detected conflicts"""
        suggestions = []
        
        for conflict in conflicts:
            asset_ids = conflict['conflicting_assets']
            
            for asset_id in asset_ids:
                asset = Asset.query.get(asset_id)
                if not asset:
                    continue
                
                # Find similar assets as alternatives
                similar_assets = Asset.query.filter(
                    Asset.category == asset.category,
                    Asset.status == 'ACTIVE',
                    Asset.id != asset_id
                ).limit(3).all()
                
                # Find available time slots
                conflicting_milestone = Milestone.query.get(conflict['milestone_id'])
                
                suggestions.append({
                    'conflict_asset_id': asset_id,
                    'conflict_asset_name': asset.name,
                    'conflicting_milestone': conflict['milestone_title'],
                    'alternatives': [{
                        'asset_id': alt.id,
                        'asset_name': alt.name,
                        'category': alt.category,
                        'specifications': alt.specifications or {}
                    } for alt in similar_assets],
                    'time_slots': AssetConflictService._find_available_time_slots(
                        asset_id, 
                        conflicting_milestone.start_date, 
                        conflicting_milestone.end_date
                    )
                })
        
        return suggestions
    
    @staticmethod
    def _find_available_time_slots(asset_id, conflict_start, conflict_end):
        """Find available time slots around conflict period"""
        # Look for slots before and after the conflict
        slots = []
        
        # Look 7 days before and after the conflict
        search_start = conflict_start - timedelta(days=7)
        search_end = conflict_end + timedelta(days=7)
        
        # Get existing assignments
        existing_assignments = db.session.query(AssetAssignment).join(Task).join(Milestone).filter(
            AssetAssignment.asset_id == asset_id,
            AssetAssignment.status.in_(['REQUESTED', 'ASSIGNED']),
            Milestone.start_date <= search_end,
            Milestone.end_date >= search_start
        ).order_by(Milestone.start_date).all()
        
        # Find gaps between assignments
        if not existing_assignments:
            # Asset is completely available
            slots.append({
                'start': search_start.isoformat(),
                'end': search_end.isoformat(),
                'duration_days': 14,
                'type': 'fully_available'
            })
        else:
            # Find gaps
            previous_end = search_start
            for assignment in existing_assignments:
                if assignment.task.milestone.start_date > previous_end:
                    gap_days = (assignment.task.milestone.start_date - previous_end).days
                    if gap_days >= 1:  # Only show gaps of 1+ days
                        slots.append({
                            'start': previous_end.isoformat(),
                            'end': assignment.task.milestone.start_date.isoformat(),
                            'duration_days': gap_days,
                            'type': 'gap_between_assignments'
                        })
                
                previous_end = assignment.task.milestone.end_date
            
            # Check after last assignment
            if previous_end < search_end:
                gap_days = (search_end - previous_end).days
                if gap_days >= 1:
                    slots.append({
                        'start': previous_end.isoformat(),
                        'end': search_end.isoformat(),
                        'duration_days': gap_days,
                        'type': 'available_after_assignments'
                    })
        
        return slots
    
    @staticmethod
    def generate_conflict_report(milestone_id):
        """Generate comprehensive conflict report for a milestone"""
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return None
        
        conflicts = AssetConflictService.check_asset_conflicts(
            milestone_id, milestone.start_date, milestone.end_date
        )
        
        if not conflicts:
            return {
                'milestone_id': milestone_id,
                'milestone_title': milestone.title,
                'conflicts_found': False,
                'message': 'No asset conflicts detected',
                'recommendations': ['Proceed with milestone planning']
            }
        
        # Get resolution suggestions
        suggestions = AssetConflictService.get_conflict_resolution_suggestions(conflicts)
        
        return {
            'milestone_id': milestone_id,
            'milestone_title': milestone.title,
            'conflicts_found': True,
            'total_conflicts': len(conflicts),
            'conflicts': conflicts,
            'suggestions': suggestions,
            'recommendations': [
                'Review alternative assets suggested below',
                'Consider adjusting milestone dates',
                'Contact RSU for additional equipment procurement'
            ],
            'urgency_level': 'HIGH' if len(conflicts) > 3 else 'MEDIUM' if len(conflicts) > 1 else 'LOW'
        }
