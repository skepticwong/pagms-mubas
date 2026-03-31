from models import db, Task, User, Grant
from datetime import datetime, date

class TaskService:
    @staticmethod
    def create_task(data, creator_id):
        grant_id = data.get('grant_id')
        assigned_to_id = data.get('assigned_to')
        title = data.get('title')
        task_type = data.get('task_type')
        deadline_str = data.get('deadline')
        estimated_hours = data.get('estimated_hours')
        pay_rate_override = data.get('pay_rate_override')
        milestone_id = data.get('milestone_id')

        if not all([grant_id, assigned_to_id, title, task_type, deadline_str]):
            raise ValueError("Missing required task fields.")

        # Convert deadline string to date object
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid deadline format. Use YYYY-MM-DD.")

        # Check if grant exists
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError(f"Grant with ID {grant_id} not found.")
        
        # Check if assigned_to user exists
        assignee = User.query.get(assigned_to_id)
        if not assignee:
            raise ValueError(f"User with ID {assigned_to_id} not found.")
            
        # Optional: Check if creator_id has permissions to create task for this grant/assignee
        # For now, we assume PI can create tasks for their grants and assign to any user.
        # This can be expanded later with more complex authorization logic.
        if grant.pi_id != creator_id:
            raise ValueError("Only the PI of this grant can create tasks for it.")

        # Check Milestone Status if provided
        if milestone_id:
            from models import Milestone
            milestone = Milestone.query.get(milestone_id)
            if not milestone:
                raise ValueError(f"Milestone with ID {milestone_id} not found.")
            if milestone.status == 'COMPLETED':
                raise ValueError("Cannot add tasks to a completed milestone. Please reopen the milestone first.")

        new_task = Task(
            grant_id=grant_id,
            assigned_to=assigned_to_id,
            title=title,
            task_type=task_type,
            deadline=deadline,
            estimated_hours=estimated_hours,
            pay_rate_override=pay_rate_override,
            milestone_id=milestone_id,
            status='assigned',
            created_at=datetime.utcnow()
        )
        db.session.add(new_task)
        db.session.commit()
        return new_task

    @staticmethod
    def get_tasks_for_user(user_id, role=None, grant_id=None, status=None):
        query = Task.query
        
        # Filter by creator/assignee based on role (or assuming PI for creation)
        # For a PI, show tasks created by them and tasks assigned to team members under their grants
        # For a Team member, show tasks assigned to them
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        if user.role == 'PI':
            # Get grants managed by this PI
            pi_grants = Grant.query.filter_by(pi_id=user_id).all()
            pi_grant_ids = [g.id for g in pi_grants]
            
            if not pi_grant_ids:
                return [] # PI has no grants, thus no tasks associated with their grants

            query = query.filter(Task.grant_id.in_(pi_grant_ids))
            
            # If a specific grant_id is provided, filter further
            if grant_id:
                if grant_id not in pi_grant_ids:
                    raise ValueError(f"Grant with ID {grant_id} is not managed by this PI.")
                query = query.filter_by(grant_id=grant_id)

        elif user.role in ['Team', 'Finance', 'RSU']: # Assuming these roles are assigned tasks
            query = query.filter_by(assigned_to=user_id)
            if grant_id:
                query = query.filter_by(grant_id=grant_id)
        else:
            return [] # No tasks for other roles yet

        if status:
            query = query.filter_by(status=status)

        tasks = query.all()
        # Enrich task data with grant title and assignee name
        result = []
        for task in tasks:
            task_dict = task.to_dict()
            task_dict['grant_title'] = task.grant.title if task.grant else 'N/A'
            task_dict['grant_code'] = task.grant.grant_code if task.grant else 'N/A'
            task_dict['assigned_to_name'] = task.assignee.name if task.assignee else 'N/A'
            task_dict['assigned_to_email'] = task.assignee.email if task.assignee else 'N/A'
            task_dict['milestone_title'] = task.milestone_ptr.title if task.milestone_ptr else None
            result.append(task_dict)
        return result

    @staticmethod
    def get_task_by_id(task_id):
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")
        task_dict = task.to_dict()
        task_dict['grant_title'] = task.grant.title if task.grant else 'N/A'
        task_dict['grant_code'] = task.grant.grant_code if task.grant else 'N/A'
        task_dict['assigned_to_name'] = task.assignee.name if task.assignee else 'N/A'
        task_dict['assigned_to_email'] = task.assignee.email if task.assignee else 'N/A'
        task_dict['milestone_title'] = task.milestone_ptr.title if task.milestone_ptr else None
        return task_dict

    @staticmethod
    def update_task(task_id, data, updater_id):
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        updater = User.query.get(updater_id)
        if not updater:
            raise ValueError(f"Updater user with ID {updater_id} not found.")

        # Authorization check: Only PI who created the task or RSU can update certain fields
        # A simpler rule for now: only the PI of the grant can update tasks
        if task.grant.pi_id != updater_id and updater.role != 'RSU':
            raise ValueError("You do not have permission to update this task.")

        # Check if task is being marked as completed
        if data.get('status') == 'COMPLETED':
            # Import here to avoid circular imports
            from services.asset_assignment_service import AssetAssignmentService
            
            # Check if all assigned assets are returned
            if not AssetAssignmentService.can_complete_task(task_id):
                # Get pending returns for detailed error message
                pending_returns = AssetAssignmentService.get_pending_returns_for_task(task_id)
                pending_assets = [
                    f"{assignment.asset.name} (assigned to {assignment.assigned_user.name if assignment.assigned_user else 'Unknown'})"
                    for assignment in pending_returns
                ]
                
                raise ValueError(
                    f"Cannot complete task - {len(pending_returns)} asset(s) must be returned first: "
                    f"{', '.join(pending_assets)}. Please ensure all equipment is returned before marking task as complete."
                )

        for key, value in data.items():
            if hasattr(task, key):
                if key == 'deadline' and isinstance(value, str):
                    try:
                        setattr(task, key, datetime.strptime(value, '%Y-%m-%d').date())
                    except ValueError:
                        raise ValueError("Invalid deadline format. Use YYYY-MM-DD.")
                elif key == 'assigned_to' or key == 'milestone_id':
                    setattr(task, key, value)
                else:
                    setattr(task, key, value)
        
        db.session.commit()
        return task

    @staticmethod
    def delete_task(task_id, deleter_id):
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        deleter = User.query.get(deleter_id)
        if not deleter:
            raise ValueError(f"Deleter user with ID {deleter_id} not found.")

        # Authorization check: Only PI who created the task or RSU can delete
        if task.grant.pi_id != deleter_id and deleter.role != 'RSU':
            raise ValueError("You do not have permission to delete this task.")

        db.session.delete(task)
        db.session.commit()
        return {"message": "Task deleted successfully"}

    @staticmethod
    def get_team_members_for_pi(pi_id):
        """
        Get all unique team members from all grants managed by this PI.
        """
        # 1. Get all grants managed by this PI
        pi_grants = Grant.query.filter_by(pi_id=pi_id).all()
        grant_ids = [g.id for g in pi_grants]
        
        if not grant_ids:
            return []

        # 2. Find all unique team members for these grants
        # We need to import GrantTeam here to avoid circular imports if any
        from models import GrantTeam
        team_entries = GrantTeam.query.filter(GrantTeam.grant_id.in_(grant_ids)).all()
        
        # Use a dict to keep users unique by ID
        unique_members = {}
        for entry in team_entries:
            if entry.user_id not in unique_members:
                unique_members[entry.user_id] = {
                    'id': entry.user.id,
                    'name': entry.user.name,
                    'email': entry.user.email,
                    'role': entry.role
                }
        
        return list(unique_members.values())

    @staticmethod
    def verify_deliverable(deliverable_id, status, approver_user_id, notes=None):
        """
        Verify a deliverable submission: approve or request revision.
        Callers must authorize the approver (e.g. routes/tasks uses can_approve_deliverable).
        """
        from models import DeliverableSubmission, AuditLog
        deliverable = DeliverableSubmission.query.get(deliverable_id)
        if not deliverable:
            raise ValueError(f"Deliverable submission with ID {deliverable_id} not found.")

        task = Task.query.get(deliverable.task_id)
        if not task:
            raise ValueError(f"Task associated with deliverable not found.")

        if status == 'approved':
            deliverable.verification_status = 'approved'
            task.status = 'COMPLETED'
            
            # If task is linked to a milestone, update milestone status
            if task.milestone_id:
                from services.milestone_service import MilestoneService
                MilestoneService.update_milestone_status(task.milestone_id)
        elif status == 'revision_requested':
            deliverable.verification_status = 'revision_requested'
            task.status = 'revision_requested'
            if notes:
                deliverable.activity_notes = (deliverable.activity_notes or "") + f"\n\nPI Revision Request: {notes}"
        else:
            raise ValueError("Invalid verification status. Use 'approved' or 'revision_requested'.")

        db.session.commit()
        return deliverable