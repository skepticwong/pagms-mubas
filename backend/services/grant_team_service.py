from models import db, Grant, User, GrantTeam
from datetime import datetime

class GrantTeamService:
    @staticmethod
    def add_team_member_to_grant(grant_id, user_id, role, caller_id):
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

        # 3. Create new GrantTeam entry
        new_member = GrantTeam(
            grant_id=grant_id,
            user_id=user_id,
            role=role,
            date_added=datetime.utcnow()
        )
        db.session.add(new_member)
        db.session.commit()
        return new_member

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