# backend/services/effort_service.py
from models import db, EffortCertification, DeliverableSubmission, Task, GrantTeam, User, Grant
from sqlalchemy import func
from datetime import datetime, date
import calendar

class EffortService:
    @staticmethod
    def _get_previous_month_period():
        today = datetime.now()
        if today.month == 1:
            return today.year - 1, 12
        return today.year, today.month - 1

    @staticmethod
    def get_uncertified_effort(user_id, grant_id, year, month):
        """
        Aggregate hours from DeliverableSubmission for a specific period.
        """
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)

        # Build query to sum hours
        # DeliverableSubmission -> Task -> Grant (via task.grant_id)
        total_hours = db.session.query(func.sum(DeliverableSubmission.hours_worked))\
            .join(Task, DeliverableSubmission.task_id == Task.id)\
            .filter(
                DeliverableSubmission.user_id == user_id,
                Task.grant_id == grant_id,
                DeliverableSubmission.submitted_at >= start_date,
                DeliverableSubmission.submitted_at <= end_date
            ).scalar() or 0.0

        # Check for existing certification
        existing = EffortCertification.query.filter_by(
            user_id=user_id,
            grant_id=grant_id,
            period_month=month,
            period_year=year
        ).first()

        return {
            'logged_hours': total_hours,
            'certification': existing.to_dict() if existing else None,
            'is_certified': existing.status == 'VERIFIED' if existing else False
        }

    @staticmethod
    def can_pi_certify(grant_id, year, month):
        """
        The "Team First" Rule:
        PI cannot certify until all team members have certified theirs.
        """
        team_members = GrantTeam.query.filter_by(grant_id=grant_id, status='active').all()
        
        for member in team_members:
            # Check if this member has a VERIFIED certification for the period
            cert = EffortCertification.query.filter_by(
                user_id=member.user_id,
                grant_id=grant_id,
                period_month=month,
                period_year=year,
                status='VERIFIED'
            ).first()
            
            if not cert:
                return False, f"Team member {member.user.name} has not certified yet."
        
        return True, "All team members have certified."

    @staticmethod
    def check_spending_lock(grant_id):
        """
        The Enforcement Gate:
        - Warn from Day 1-9 of the new month for the previous month's effort.
        - Hard Lock on Day 10+.
        Returns: (is_locked, message, severity)
        """
        today = datetime.now()
        day = today.day
        prev_year, prev_month = EffortService._get_previous_month_period()

        # Get PI's certification for the previous month
        # Note: We only lock if the PI hasn't certified. 
        # (Implicitly, PI can't certify if team hasn't, so this covers everyone).
        grant = Grant.query.get(grant_id)
        if not grant:
            return False, "Grant not found", "info"

        cert = EffortCertification.query.filter_by(
            user_id=grant.pi_id,
            grant_id=grant_id,
            period_month=prev_month,
            period_year=prev_year,
            status='VERIFIED'
        ).first()

        if cert or (cert and cert.is_rsu_overridden):
            return False, "Compliant", "success"

        # Check for RSU override independently if cert object doesn't exist
        override = EffortCertification.query.filter_by(
            grant_id=grant_id,
            period_month=prev_month,
            period_year=prev_year,
            is_rsu_overridden=True
        ).first()
        if override:
            return False, "RSU Override Active", "success"

        month_name = calendar.month_name[prev_month]
        if day >= 10:
            return True, f"Spending Locked: Effort certification for {month_name} {prev_year} is overdue.", "error"
        else:
            return False, f"Warning: Effort certification for {month_name} {prev_year} is due by the 10th.", "warning"

    @staticmethod
    def get_period_compliance(grant_id, year, month):
        """
        Return compliance status for an arbitrary period.
        Locking logic only applies to the previous month.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            return False, "Grant not found", "info"

        cert = EffortCertification.query.filter_by(
            user_id=grant.pi_id,
            grant_id=grant_id,
            period_month=month,
            period_year=year,
            status='VERIFIED'
        ).first()
        if cert:
            return False, f"Compliant: Effort certified for {calendar.month_name[month]} {year}.", "success"

        override = EffortCertification.query.filter_by(
            grant_id=grant_id,
            period_month=month,
            period_year=year,
            is_rsu_overridden=True
        ).first()
        if override:
            return False, f"RSU Override Active for {calendar.month_name[month]} {year}.", "success"

        prev_year, prev_month = EffortService._get_previous_month_period()
        if year == prev_year and month == prev_month:
            # Keep existing enforcement behavior for the compliance month.
            return EffortService.check_spending_lock(grant_id)

        return False, f"Not yet certified for {calendar.month_name[month]} {year}.", "warning"

    @staticmethod
    def certify_effort(user_id, grant_id, year, month, percentage, signature, ip, is_pi=False):
        """
        Create or update an effort certification.
        """
        # If PI, check Team First rule
        if is_pi:
            allowed, msg = EffortService.can_pi_certify(grant_id, year, month)
            if not allowed:
                raise ValueError(msg)

        # Get logged hours for reference
        stats = EffortService.get_uncertified_effort(user_id, grant_id, year, month)
        
        cert = EffortCertification.query.filter_by(
            user_id=user_id,
            grant_id=grant_id,
            period_month=month,
            period_year=year
        ).first()

        if not cert:
            cert = EffortCertification(
                user_id=user_id,
                grant_id=grant_id,
                period_month=month,
                period_year=year,
                certification_period=f"{year}-{month:02d}"
            )
            db.session.add(cert)

        cert.logged_hours = stats['logged_hours']
        cert.certified_percentage = percentage
        cert.signature_text = signature
        cert.ip_address = ip
        cert.certified_at = datetime.utcnow()
        cert.status = 'VERIFIED' # For now auto-verified on submission, usually RSU might review
        cert.is_pi_certification = is_pi
        
        db.session.commit()
        return cert

    @staticmethod
    def apply_override(grant_id, year, month, justification):
        """
        RSU Override to unlock a grant.
        """
        cert = EffortCertification.query.filter_by(
            grant_id=grant_id,
            period_month=month,
            period_year=year,
            is_pi_certification=True # Override usually targets the PI's block
        ).first()

        if not cert:
            # Create a placeholder cert just for the override
            # We need a user_id, we'll use the PI's ID
            grant = Grant.query.get(grant_id)
            cert = EffortCertification(
                user_id=grant.pi_id,
                grant_id=grant_id,
                period_month=month,
                period_year=year,
                certification_period=f"{year}-{month:02d}",
                status='PENDING', # Keep as pending but overridden
                is_pi_certification=True
            )
            db.session.add(cert)

        cert.is_rsu_overridden = True
        cert.override_justification = justification
        db.session.commit()
        return cert
