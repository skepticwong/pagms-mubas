import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from models import db, Grant, BudgetCategory, Milestone, AuditLog

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

class GrantService:
    @staticmethod
    def _save_file(file_storage, subfolder=''):
        """Helper to save a file and return the filename."""
        if not file_storage or not file_storage.filename:
            return None
            
        filename = secure_filename(file_storage.filename)
        # Unique prefix to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        path = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(path, exist_ok=True)
        
        file_storage.save(os.path.join(path, unique_filename))
        return unique_filename

    @staticmethod
    def create_grant(data, files, user_id):
        """
        Creates a grant from multipart/form-data.
        :param data: dict (request.form)
        :param files: dict (request.files)
        :param user_id: int
        :return: Grant object
        """
        try:
            # 1. Basic Fields
            grant = Grant(
                title=data.get('title'),
                funder=data.get('funder'),
                grant_code=data.get('grant_code'),
                funder_reference_number=data.get('funder_reference_number'),
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
                total_budget=float(data.get('total_budget')),
                currency=data.get('currency', 'USD'),
                exchange_rate=float(data.get('exchange_rate', 1.0)),
                financial_reporting_frequency=data.get('financial_reporting_frequency'),
                progress_reporting_frequency=data.get('progress_reporting_frequency'),
                special_requirements=data.get('special_requirements'),
                pi_id=user_id,
                status='pending'
            )

            # 2. File Uploads
            grant.agreement_filename = GrantService._save_file(files.get('agreement'), 'agreements')
            grant.budget_breakdown_filename = GrantService._save_file(files.get('budget_breakdown'), 'documents')
            grant.award_letter_filename = GrantService._save_file(files.get('award_letter'), 'documents')
            grant.ethical_approval_filename = GrantService._save_file(files.get('ethical_approval'), 'documents')

            db.session.add(grant)
            db.session.flush() # Generate ID

            # 3. Budget Categories (JSON string)
            categories_json = data.get('budget_categories')
            if categories_json:
                categories = json.loads(categories_json)
                for cat in categories:
                    db.session.add(BudgetCategory(
                        grant_id=grant.id,
                        name=cat['name'],
                        allocated=float(cat['allocated'])
                    ))

            # 4. Milestones (JSON string)
            milestones_json = data.get('milestones')
            if milestones_json:
                milestones = json.loads(milestones_json)
                for i, m in enumerate(milestones):
                    milestone = Milestone(
                        grant_id=grant.id,
                        title=m['title'],
                        description=m.get('description'),
                        due_date=datetime.strptime(m['due_date'], '%Y-%m-%d').date(),
                        reporting_period=m.get('reporting_period'),
                        status=m.get('status', 'not_started')
                    )
                    # Handle specific milestone evidence file (milestone_evidence_0, etc.)
                    evidence_file = files.get(f"milestone_evidence_{i}")
                    if evidence_file:
                       milestone.evidence_filename = GrantService._save_file(evidence_file, 'evidence')
                       
                    db.session.add(milestone)

            # 5. Audit Log
            db.session.add(AuditLog(
                user_id=user_id,
                action='grant_created',
                resource_type='grant',
                resource_id=grant.id,
                details=f'Grant "{grant.title}" initialized (Pending Approval)'
            ))

            db.session.commit()
            return grant

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def approve_grant(grant_id, user_id):
        """
        Approves a pending grant.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")
        
        if grant.status == 'active':
            return grant # Already active

        grant.status = 'active'
        
        # Log Audit
        db.session.add(AuditLog(
            user_id=user_id,
            action='grant_approved',
            resource_type='grant',
            resource_id=grant.id,
            details=f'Grant "{grant.title}" approved by RSU'
        ))
        
        db.session.commit()
        return grant

    @staticmethod
    def get_grants_for_user(user_id):
        """
        Get all grants.
        - If RSU: Returns ALL grants.
        - If PI: Returns grants where they are PI.
        """
        print(f"DEBUG: get_grants_for_user called with user_id: {user_id}") # DEBUG PRINT
        from models import User # Avoid circular import
        user = User.query.get(user_id)
        print(f"DEBUG: User object for user_id {user_id}: {user}") # DEBUG PRINT
        if user:
            print(f"DEBUG: User role for user_id {user_id}: {user.role}") # DEBUG PRINT
        
        if user and user.role == 'RSU':
            grants = Grant.query.order_by(Grant.created_at.desc()).all()
        elif user and user.role == 'PI':
            grants = Grant.query.filter_by(pi_id=user_id).order_by(Grant.created_at.desc()).all()
        elif user and user.role == 'Team':
            from models import GrantTeam
            # Get grants where user is a team member
            team_entries = GrantTeam.query.filter_by(user_id=user_id).all()
            grant_ids = [entry.grant_id for entry in team_entries]
            grants = Grant.query.filter(Grant.id.in_(grant_ids)).order_by(Grant.created_at.desc()).all()
        else:
            grants = []

        results = []
        
        for grant in grants:
            # 1. Calculate Financials
            # Sum of spent from all categories
            total_spent = sum(cat.spent for cat in grant.categories)
            spent_percent = 0
            if grant.total_budget > 0:
                spent_percent = round((total_spent / grant.total_budget) * 100)
            
            # 2. Find Next Deadline (from Milestones)
            # Find the earliest incomplete milestone due in the future
            next_milestone = Milestone.query.filter(
                Milestone.grant_id == grant.id,
                Milestone.status != 'completed',
                Milestone.due_date >= datetime.today().date()
            ).order_by(Milestone.due_date.asc()).first()
            
            next_deadline_date = next_milestone.due_date if next_milestone else None
            next_deadline_label = next_milestone.title if next_milestone else "No upcoming deadlines"

            # 3. Format Data
            data = grant.to_dict(include_categories=True)
            data.update({
                'spent_percent': spent_percent,
                'total_mwk': grant.total_budget * grant.exchange_rate,
                'next_deadline_date': next_deadline_date.isoformat() if next_deadline_date else None,
                'next_deadline_label': next_deadline_label,
                'exchange_rate_label': f"1 {grant.currency} = {grant.exchange_rate} MWK"
            })
            results.append(data)
            
        print(f"DEBUG: get_grants_for_user returning {len(results)} grants for user_id {user_id} with role {user.role}") # DEBUG PRINT
        return results