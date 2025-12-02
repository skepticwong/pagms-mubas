# backend/services/grant_service.py
from models import db, Grant, User
from datetime import datetime

class GrantService:
    @staticmethod
    def create_grant(title, funder, start_date, end_date, total_budget, pi_id=None):
        """
        Create a new grant with validation
        Returns Grant object
        Raises ValueError on validation errors
        """
        # Validation
        if not all([title, funder, start_date, end_date, total_budget]):
            raise ValueError("Missing required fields")
        
        if total_budget <= 0:
            raise ValueError("Total budget must be greater than 0")
        
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
        
        # Get PI (or use provided pi_id)
        if pi_id:
            pi = User.query.get(pi_id)
            if not pi:
                raise ValueError("PI not found")
        else:
            pi = User.query.filter_by(role='PI').first()
            if not pi:
                raise ValueError("No PI found in system")
        
        # Create grant
        grant = Grant(
            title=title,
            funder=funder,
            start_date=start_date,
            end_date=end_date,
            total_budget=total_budget,
            pi_id=pi.id
        )
        db.session.add(grant)
        db.session.commit()
        return grant

    @staticmethod
    def get_all_grants():
        """
        Get all grants
        Returns list of Grant objects
        """
        return Grant.query.all()

    @staticmethod
    def get_grant_by_id(grant_id):
        """
        Get grant by ID
        Returns Grant object or None
        """
        if not grant_id:
            return None
        return Grant.query.get(grant_id)