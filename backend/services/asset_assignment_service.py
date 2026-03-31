# services/asset_assignment_service.py
from datetime import datetime
from models import db, AssetAssignment, Asset, Task, User
from flask import request

class AssetAssignmentService:
    """Service for managing asset assignments to tasks"""
    
    @staticmethod
    def validate_milestone_assets(milestone_id):
        """Validate all assets are returned for milestone completion"""
        from models import Task
        # Get all tasks under this milestone
        tasks = Task.query.filter_by(milestone_id=milestone_id).all()
        
        for task in tasks:
            # Check if task has unreturned assets
            pending_returns = AssetAssignmentService.get_pending_returns_for_task(task.id)
            if pending_returns:
                asset_names = [assignment.asset.name for assignment in pending_returns]
                return False, f"Task '{task.title}' has {len(pending_returns)} unreturned assets: {', '.join(asset_names)}"
        
        return True, "All assets returned"
    
    @staticmethod
    def get_milestone_assets(milestone_id):
        """Get all asset assignments for a milestone"""
        from models import Task
        tasks = Task.query.filter_by(milestone_id=milestone_id).all()
        all_assignments = []
        
        for task in tasks:
            assignments = AssetAssignment.query.filter_by(task_id=task.id).all()
            all_assignments.extend(assignments)
        
        return all_assignments
    
    @staticmethod
    def get_pending_returns_for_task(task_id):
        """Get pending returns for a specific task"""
        return AssetAssignment.query.filter_by(
            task_id=task_id,
            status='ASSIGNED'
        ).all()
    
    @staticmethod
    def reserve_assets_for_milestone(milestone_id, asset_requirements, requesting_user_id):
        """Reserve assets for an upcoming milestone"""
        from models import Milestone
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            raise ValueError("Milestone not found")
        
        # Check for conflicts
        from services.asset_conflict_service import AssetConflictService
        conflicts = AssetConflictService.check_asset_conflicts(
            milestone_id, milestone.start_date, milestone.end_date
        )
        
        if conflicts:
            conflict_assets = []
            for conflict in conflicts:
                conflict_assets.extend(conflict['conflicting_assets'])
            
            raise ValueError(f"Asset conflicts detected: {len(set(conflict_assets))} assets have scheduling conflicts")
        
        # Create reservations (assignments with REQUESTED status)
        reservations = []
        for req in asset_requirements:
            asset = Asset.query.get(req['asset_id'])
            if not asset:
                raise ValueError(f"Asset with ID {req['asset_id']} not found")
            
            # Check if asset is available
            if asset.status not in ['ACTIVE', 'AVAILABLE']:
                raise ValueError(f"Asset {asset.name} is not available for reservation")
            
            # Create reservation
            reservation = AssetAssignment(
                task_id=None,  # Will be assigned to specific task later
                asset_id=asset.id,
                assigned_to_user_id=requesting_user_id,
                notes=f"Reserved for milestone: {milestone.title}. {req.get('notes', '')}"
            )
            
            db.session.add(reservation)
            reservations.append(reservation)
        
        db.session.commit()
        return reservations
    
    @staticmethod
    def checkout_asset_to_user(assignment_id, user_id, pickup_evidence=None):
        """Check out asset to specific user"""
        assignment = AssetAssignment.query.get(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")
        
        if assignment.assigned_to_user_id != user_id:
            raise ValueError("Asset not assigned to this user")
        
        if assignment.status != 'REQUESTED':
            raise ValueError("Asset is not in REQUESTED status")
        
        # Update assignment
        assignment.status = 'ASSIGNED'
        assignment.assigned_at = datetime.utcnow()
        assignment.pickup_confirmed_by = user_id
        if pickup_evidence:
            assignment.pickup_evidence_doc = pickup_evidence
        
        db.session.commit()
        return assignment
    
    @staticmethod
    def get_user_asset_checkout_history(user_id, start_date=None, end_date=None):
        """Get checkout history for a user"""
        query = AssetAssignment.query.filter_by(assigned_to_user_id=user_id)
        
        if start_date:
            query = query.filter(AssetAssignment.assigned_at >= start_date)
        if end_date:
            query = query.filter(AssetAssignment.assigned_at <= end_date)
        
        return query.order_by(AssetAssignment.assigned_at.desc()).all()
    
    @staticmethod
    def get_asset_checkout_statistics(asset_id, start_date=None, end_date=None):
        """Get checkout statistics for a specific asset"""
        query = AssetAssignment.query.filter_by(asset_id=asset_id)
        
        if start_date:
            query = query.filter(AssetAssignment.assigned_at >= start_date)
        if end_date:
            query = query.filter(AssetAssignment.assigned_at <= end_date)
        
        assignments = query.all()
        
        total_checkouts = len(assignments)
        active_checkouts = len([a for a in assignments if a.status == 'ASSIGNED'])
        avg_checkout_duration = 0
        
        if total_checkouts > 0:
            completed_checkouts = [a for a in assignments if a.returned_at]
            if completed_checkouts:
                total_duration = sum([
                    (a.returned_at - a.assigned_at).days for a in completed_checkouts
                ])
                avg_checkout_duration = total_duration / len(completed_checkouts)
        
        return {
            'asset_id': asset_id,
            'total_checkouts': total_checkouts,
            'active_checkouts': active_checkouts,
            'completed_checkouts': total_checkouts - active_checkouts,
            'average_checkout_duration_days': round(avg_checkout_duration, 1),
            'utilization_rate': round((total_checkouts / 30) * 100, 1) if total_checkouts > 0 else 0  # Assuming 30-day period
        }
    
    @staticmethod
    def request_assets_for_task(task_id, asset_requirements, requesting_user_id):
        """Create asset requests for a task
        
        Args:
            task_id: ID of the task
            asset_requirements: List of dicts with asset_id, quantity, notes
            requesting_user_id: ID of user making the request
            
        Returns:
            List of created AssetAssignment objects
        """
        try:
            # Verify user has permission to assign assets to this task
            task = Task.query.get(task_id)
            if not task:
                raise ValueError("Task not found")
            
            # Check if user is PI of the grant or assigned to the task
            if task.grant.pi_id != requesting_user_id and task.assigned_to != requesting_user_id:
                raise ValueError("Only PI or assigned user can request assets for this task")
            
            assignments = []
            for req in asset_requirements:
                asset = Asset.query.get(req['asset_id'])
                if not asset:
                    raise ValueError(f"Asset with ID {req['asset_id']} not found")
                
                # Check if asset is available
                if asset.status not in ['ACTIVE', 'AVAILABLE']:
                    raise ValueError(f"Asset {asset.name} is not available for assignment")
                
                # Create assignment
                assignment = AssetAssignment(
                    task_id=task_id,
                    asset_id=asset.id,
                    assigned_to_user_id=task.assigned_to,  # Assign to task assignee
                    notes=req.get('notes', '')
                )
                
                db.session.add(assignment)
                assignments.append(assignment)
                
                # Update asset status to show it's requested
                asset.status = 'REQUESTED'
            
            db.session.commit()
            return assignments
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def confirm_asset_pickup(assignment_id, user_id, evidence_doc=None):
        """Team member confirms they've picked up the asset
        
        Args:
            assignment_id: ID of the asset assignment
            user_id: ID of user confirming pickup
            evidence_doc: Optional path to pickup evidence (photo/QR scan)
            
        Returns:
            Updated AssetAssignment object
        """
        try:
            assignment = AssetAssignment.query.get(assignment_id)
            if not assignment:
                raise ValueError("Assignment not found")
            
            # Verify user is the assigned user
            if assignment.assigned_to_user_id != user_id:
                raise ValueError("Only assigned user can confirm pickup")
            
            # Update assignment
            assignment.status = 'ASSIGNED'
            assignment.assigned_at = datetime.utcnow()
            assignment.pickup_confirmed_by = user_id
            assignment.pickup_evidence_doc = evidence_doc
            
            # Update asset status
            asset = assignment.asset
            asset.status = 'IN_USE'
            asset.custodian_user_id = user_id
            asset.assigned_task_id = assignment.task_id
            
            db.session.commit()
            return assignment
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def confirm_asset_return(assignment_id, user_id, evidence_doc=None):
        """Team member confirms asset return
        
        Args:
            assignment_id: ID of the asset assignment
            user_id: ID of user confirming return
            evidence_doc: Optional path to return evidence (photo/handover proof)
            
        Returns:
            Updated AssetAssignment object
        """
        try:
            assignment = AssetAssignment.query.get(assignment_id)
            if not assignment:
                raise ValueError("Assignment not found")
            
            # Verify user is the assigned user
            if assignment.assigned_to_user_id != user_id:
                raise ValueError("Only assigned user can confirm return")
            
            # Update assignment
            assignment.status = 'RETURNED'
            assignment.returned_at = datetime.utcnow()
            assignment.return_confirmed_by = user_id
            assignment.return_evidence_doc = evidence_doc
            
            # Update asset status
            asset = assignment.asset
            asset.status = 'ACTIVE'
            asset.custodian_user_id = None
            asset.assigned_task_id = None
            
            db.session.commit()
            return assignment
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_pending_returns_for_user(user_id):
        """Get assets user needs to return
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of AssetAssignment objects with status 'ASSIGNED'
        """
        return AssetAssignment.query.filter_by(
            assigned_to_user_id=user_id,
            status='ASSIGNED'
        ).all()
    
    @staticmethod
    def get_pending_returns_for_task(task_id):
        """Get assets not returned for a specific task
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of AssetAssignment objects with status 'ASSIGNED'
        """
        return AssetAssignment.query.filter_by(
            task_id=task_id,
            status='ASSIGNED'
        ).all()
    
    @staticmethod
    def can_complete_task(task_id):
        """Check if all assigned assets are returned
        
        Args:
            task_id: ID of the task
            
        Returns:
            Boolean indicating if task can be completed
        """
        pending_returns = AssetAssignment.query.filter_by(
            task_id=task_id,
            status='ASSIGNED'
        ).count()
        
        return pending_returns == 0
    
    @staticmethod
    def get_task_asset_assignments(task_id):
        """Get all asset assignments for a task
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of AssetAssignment objects
        """
        return AssetAssignment.query.filter_by(task_id=task_id).all()
    
    @staticmethod
    def get_user_assignment_history(user_id):
        """Get assignment history for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of AssetAssignment objects for this user
        """
        return AssetAssignment.query.filter_by(
            assigned_to_user_id=user_id
        ).order_by(AssetAssignment.created_at.desc()).all()
    
    @staticmethod
    def get_available_assets_for_grant(grant_id):
        """Get available assets for a grant
        
        Args:
            grant_id: ID of the grant
            
        Returns:
            List of Asset objects that are available
        """
        return Asset.query.filter_by(
            grant_id=grant_id,
            status='ACTIVE'
        ).all()
    
    @staticmethod
    def get_asset_utilization_metrics(grant_id, start_date=None, end_date=None):
        """Calculate asset utilization metrics for a grant
        
        Args:
            grant_id: ID of the grant
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dictionary with utilization metrics
        """
        try:
            # Get all tasks for the grant within date range
            query = Task.query.filter_by(grant_id=grant_id)
            if start_date:
                query = query.filter(Task.created_at >= start_date)
            if end_date:
                query = query.filter(Task.created_at <= end_date)
            
            tasks = query.all()
            task_ids = [task.id for task in tasks]
            
            # Get all assignments for these tasks
            assignments = AssetAssignment.query.filter(
                AssetAssignment.task_id.in_(task_ids)
            ).all()
            
            # Calculate metrics
            total_tasks = len(tasks)
            tasks_with_assets = len(set(assignment.task_id for assignment in assignments))
            
            # Asset utilization rate
            utilization_rate = (tasks_with_assets / total_tasks * 100) if total_tasks > 0 else 0
            
            # Asset turnaround time (average days from assignment to return)
            returned_assignments = [a for a in assignments if a.returned_at and a.assigned_at]
            turnaround_times = [
                (a.returned_at - a.assigned_at).days 
                for a in returned_assignments
            ]
            avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
            
            # Missing asset risk
            missing_assets = AssetAssignment.query.filter(
                AssetAssignment.task_id.in_(task_ids),
                AssetAssignment.status == 'ASSIGNED'
            ).count()
            
            return {
                'asset_utilization_rate': round(utilization_rate, 2),
                'asset_turnaround_time': round(avg_turnaround, 2),
                'missing_asset_risk': missing_assets,
                'total_assignments': len(assignments),
                'returned_assignments': len(returned_assignments),
                'tasks_with_assets': tasks_with_assets,
                'total_tasks': total_tasks
            }
            
        except Exception as e:
            print(f"Error calculating utilization metrics: {e}")
            return {
                'asset_utilization_rate': 0,
                'asset_turnaround_time': 0,
                'missing_asset_risk': 0,
                'total_assignments': 0,
                'returned_assignments': 0,
                'tasks_with_assets': 0,
                'total_tasks': 0
            }
