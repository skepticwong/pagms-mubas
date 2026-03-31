from models import Task, Milestone, Asset, GrantTeam, User
from datetime import datetime, date
import calendar

class DeadlineService:
    @staticmethod
    def get_user_deadlines(user_id):
        """
        Aggregates deadlines from Tasks, Milestones, and Assets for a specific user.
        Also includes recurring institutional deadlines.
        """
        deadlines = []
        user = User.query.get(user_id)
        if not user:
            return []

        # 1. Tasks assigned to user
        tasks = Task.query.filter_by(assigned_to=user_id).filter(Task.status != 'COMPLETED').all()
        for task in tasks:
            if task.deadline:
                deadlines.append({
                    'id': f"task-{task.id}",
                    'type': 'TASK',
                    'title': task.title,
                    'date': task.deadline.isoformat(),
                    'priority': 'HIGH' if (task.deadline - datetime.now()).days < 3 else 'MEDIUM',
                    'details': f"Grant: {task.grant.title if task.grant else 'N/A'}",
                    'link': f"/tasks"
                })

        # 2. Milestones for grants the user is part of
        # Get grant IDs where user is a team member
        team_memberships = GrantTeam.query.filter_by(user_id=user_id, status='active').all()
        grant_ids = [m.grant_id for m in team_memberships]
        
        # Also include grants where user is PI (if they have dual roles or if PI uses this)
        pi_grants = User.query.get(user_id).grants_as_pi
        grant_ids.extend([g.id for g in pi_grants])
        grant_ids = list(set(grant_ids)) # Unique IDs

        milestones = Milestone.query.filter(Milestone.grant_id.in_(grant_ids), Milestone.status != 'COMPLETED').all()
        for milestone in milestones:
            if milestone.due_date:
                deadlines.append({
                    'id': f"milestone-{milestone.id}",
                    'type': 'MILESTONE',
                    'title': f"Milestone: {milestone.title}",
                    'date': milestone.due_date.isoformat(),
                    'priority': 'URGENT' if (milestone.due_date - datetime.now()).days < 7 else 'MEDIUM',
                    'details': f"Grant: {milestone.grant.title if milestone.grant else 'N/A'}",
                    'link': f"/milestones"
                })

        # 3. Assets in user's custody
        assets = Asset.query.filter_by(custodian_user_id=user_id).all()
        for asset in assets:
            if hasattr(asset, 'expected_return_date') and asset.expected_return_date:
                deadlines.append({
                    'id': f"asset-{asset.id}",
                    'type': 'ASSET_RETURN',
                    'title': f"Return {asset.name} ({asset.asset_tag})",
                    'date': asset.expected_return_date.isoformat(),
                    'priority': 'HIGH' if (asset.expected_return_date - datetime.now()).days < 2 else 'LOW',
                    'details': f"Asset Tag: {asset.asset_tag}",
                    'link': f"/inventory"
                })

        # 4. Effort Certification (Recurring on the 10th)
        now = datetime.now()
        certification_date = datetime(now.year, now.month, 10, 23, 59, 59)
        # If the 10th has already passed this month, show next month's
        if now.day > 10:
            if now.month == 12:
                certification_date = datetime(now.year + 1, 1, 10, 23, 59, 59)
            else:
                certification_date = datetime(now.year, now.month + 1, 10, 23, 59, 59)
        
        deadlines.append({
            'id': f"certification-{certification_date.strftime('%Y-%m')}",
            'type': 'COMPLIANCE',
            'title': "Effort Certification Deadline",
            'date': certification_date.isoformat(),
            'priority': 'URGENT',
            'details': "All monthly effort must be signed by the 10th.",
            'link': "/effort"
        })

        # Sort by date
        deadlines.sort(key=lambda x: x['date'])
        
        return deadlines
