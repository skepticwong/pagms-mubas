from models import db, Grant, User, GrantTeam, PriorApprovalRequest
from datetime import datetime
from services.rule_service import RuleService
from services.audit_service import AuditService
from services.health_score_service import HealthScoreService

class GrantTeamService:
    @staticmethod
    def add_team_member_to_grant(grant_id, user_id, role, caller_id, budget_authority=False):
        # 1. Authorization: Only the PI of the grant can add team members
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError(f"Grant with ID {grant_id} not found.")
        if grant.pi_id != caller_id:
            raise ValueError("You are not authorized to add team members to this grant.")
        
        # 2. Validate User and Role
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")
        
        # Ensure the user is not a PI or RSU (they are managed differently)
        if user.role in ['PI', 'RSU']:
            raise ValueError("PIs and RSU Admins cannot be added as team members to a grant via this function.")

        # Check if the user is already on the team for this grant
        existing_entry = GrantTeam.query.filter_by(grant_id=grant_id, user_id=user_id).first()
        if existing_entry:
            if existing_entry.role == role:
                return existing_entry # Already exists with the same role
            else:
                # Update role if different
                existing_entry.role = role
                db.session.commit()
                return existing_entry

        # 3. Rule Engine Evaluation (Compliance Check 2.0)
        member_data = {
            'role': role,
            'user_id': user_id,
            'user_name': user.name,
            'user_email': user.email,
            'action_type': 'PERSONNEL_ADDITION'
        }
        rule_result = RuleService.evaluate_action('PERSONNEL', member_data, grant_id, user_id=caller_id)
        
        if rule_result['outcome'] == 'BLOCK':
            reasons = "; ".join([r['guidance_text'] for r in rule_result['triggered_rules']])
            raise ValueError(f"Compliance Block: {reasons}")

        final_status = 'active'
        if rule_result['outcome'] == 'PRIOR_APPROVAL':
            final_status = 'awaiting_prior_approval'

        # 4. Create new GrantTeam entry
        new_member = GrantTeam(
            grant_id=grant_id,
            user_id=user_id,
            role=role,
            date_added=datetime.utcnow(),
            status=final_status,
            budget_authority=budget_authority
        )
        db.session.add(new_member)
        db.session.flush() # Get ID

        # 6. Forensic Audit & Health Update
        AuditService.log_action(
            user_id=caller_id,
            action='TEAM_MEMBER_ADDED',
            entity_type='PERSONNEL',
            entity_id=new_member.id,
            details={
                'member_user_id': user_id,
                'role': role,
                'outcome': rule_result['outcome']
            }
        )
        
        # Update health for significant events
        if rule_result['outcome'] in ['BLOCK', 'PRIOR_APPROVAL', 'WARN']:
            HealthScoreService.calculate_score(grant_id)
        
        db.session.commit()
        return new_member

    @staticmethod
    def preview_add_team_member(grant_id, user_id, role, caller_id):
        """Dry run for personnel change to see compliance impact."""
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError(f"Grant with ID {grant_id} not found.")
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        member_data = {
            'role': role,
            'user_id': user_id,
            'user_name': user.name,
            'action_type': 'PERSONNEL_ADDITION'
        }
        return RuleService.evaluate_action('PERSONNEL', member_data, grant_id, user_id=caller_id)

    @staticmethod
    def remove_team_member_from_grant(grant_id, user_id, caller_id):
        # 1. Authorization: Only the PI of the grant can remove team members
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError(f"Grant with ID {grant_id} not found.")
        if grant.pi_id != caller_id:
            raise ValueError("You are not authorized to remove team members from this grant.")

        # 2. Find and delete the GrantTeam entry
        member_entry = GrantTeam.query.filter_by(grant_id=grant_id, user_id=user_id).first()
        if not member_entry:
            raise ValueError(f"User with ID {user_id} is not a member of grant with ID {grant_id}.")
        
        # Prevent removing the PI of the grant (though they shouldn't be in GrantTeam)
        if member_entry.user.id == grant.pi_id:
            raise ValueError("Cannot remove the Principal Investigator of the grant.")

        db.session.delete(member_entry)
        db.session.commit()
        return {"message": "Team member removed successfully."}

    @staticmethod
    def get_team_members_for_grant(grant_id, caller_id):
        # 1. Authorization: Only PI of the grant or RSU can view team members
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError(f"Grant with ID {grant_id} not found.")
        
        caller = User.query.get(caller_id)
        if not caller:
            raise ValueError("Caller not found.")
        
        if grant.pi_id != caller_id and caller.role != 'RSU':
            raise ValueError("You are not authorized to view team members for this grant.")

        # 2. Fetch team members
        team_members_entries = GrantTeam.query.filter_by(grant_id=grant_id).all()
        
        results = []
        for entry in team_members_entries:
            member_data = entry.to_dict()
            results.append(member_data)
        
        return results

    @staticmethod
    def get_available_users_for_grant_team(caller_id):
        # 1. Authorization: Only PIs can get available users for their grants
        caller = User.query.get(caller_id)
        if not caller or caller.role != 'PI':
            raise ValueError("You are not authorized to view available users for team assignments.")

        # 2. Fetch all users who are not PIs or RSU (as they have distinct roles)
        # and are not already in some specific grant team.
        # This is a general list, actual assignment will check against specific grant
        available_users = User.query.filter(User.role.notin_(['PI', 'RSU'])).all()
        
        results = []
        for user in available_users:
            results.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role # This will be their general system role, not grant-specific
            })
        return results