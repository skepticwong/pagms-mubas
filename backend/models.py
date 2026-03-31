# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # PI, Team, Finance, RSU
    pay_rate = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert User object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'pay_rate': self.pay_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Grant(db.Model):
    __tablename__ = 'grants'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    funder = db.Column(db.String(100), nullable=True) # Deprecated: use funder_id
    funder_id = db.Column(db.Integer, db.ForeignKey('funder_profiles.id'))
    grant_code = db.Column(db.String(100), unique=True, nullable=False)
    funder_reference_number = db.Column(db.String(120))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_budget = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    exchange_rate = db.Column(db.Float, default=1.0)
    agreement_filename = db.Column(db.String(200))
    budget_breakdown_filename = db.Column(db.String(200))
    award_letter_filename = db.Column(db.String(200))
    pi_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pi = db.relationship('User', backref='grants_as_pi')
    status = db.Column(db.String(20), default='pending')
    
    # New fields for initialization
    financial_reporting_frequency = db.Column(db.String(50))
    progress_reporting_frequency = db.Column(db.String(50))
    special_requirements = db.Column(db.Text)
    ethical_approval_filename = db.Column(db.String(200))
    reporting_template_filename = db.Column(db.String(200), nullable=True) # Custom template for this grant
    indirect_cost_rate = db.Column(db.Float, default=0.0) # Percentage (e.g., 10.0 for 10%)
    
    # Ethics Compliance Fields
    ethics_required = db.Column(db.Boolean, default=False)
    ethics_status = db.Column(db.String(30), default='NOT_SUBMITTED') # NOT_SUBMITTED, PENDING_ETHICS, PENDING_MEETING, VERIFIED, REJECTED, EXPIRED, SUSPENDED_ETHICS
    ethics_expiry_date = db.Column(db.Date, nullable=True)
    ethics_approval_number = db.Column(db.String(100), nullable=True)
    ethics_certificate_filename = db.Column(db.String(255), nullable=True)  # Uploaded PDF for renewals
    
    # Immutable Archive Fields Phase 2
    archive_hash = db.Column(db.String(64), nullable=True) # SHA-256 hex string
    archived_at = db.Column(db.DateTime, nullable=True)

    # Rules Engine Links
    rule_profile_id = db.Column(db.Integer, db.ForeignKey('funder_profiles.id'))
    rule_snapshot_id = db.Column(db.Integer, db.ForeignKey('rule_snapshots.id'))

    # Relationships
    funder_profile = db.relationship('FunderProfile', foreign_keys=[funder_id], backref='grants_as_funder')
    rule_profile = db.relationship('FunderProfile', foreign_keys=[rule_profile_id], backref='grants_as_profile')
    rule_snapshot = db.relationship('RuleSnapshot', foreign_keys=[rule_snapshot_id], backref=db.backref('grant', uselist=False))

    # Disbursed Funds (Actual cash released to the institution)
    disbursed_funds = db.Column(db.Float, default=0.0)
    disbursement_type = db.Column(db.String(20), default='tranches') # single, tranches, milestone_based

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    categories = db.relationship(
        'BudgetCategory', backref='grant', lazy=True, cascade='all, delete-orphan'
    )
    
    @property
    def project_progress_percentage(self):
        """Task-weighted project progress: (total completed tasks / total tasks) * 100"""
        all_tasks = self.tasks_list
        if not all_tasks:
            # If no tasks, we check milestones. If all milestones are COMPLETED without tasks, it's 100%.
            # But usually a grant without tasks is 0% unless it has COMPLETED milestones.
            milestones_list = self.milestones_list
            if not milestones_list:
                return 0
            completed_milestones = sum(1 for m in milestones_list if m.status == 'COMPLETED')
            return int((completed_milestones / len(milestones_list)) * 100) if len(milestones_list) > 0 else 0
            
        completed_tasks = sum(1 for t in all_tasks if t.status.upper() == 'COMPLETED')
        return int((completed_tasks / len(all_tasks)) * 100) if len(all_tasks) > 0 else 0

    def to_dict(self, include_categories: bool = False):
        """Convert Grant object to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'title': self.title,
            'funder': self.funder_profile.name if self.funder_profile else self.funder,
            'grant_code': self.grant_code,
            'funder_reference_number': self.funder_reference_number,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'total_budget': self.total_budget,
            'currency': self.currency,
            'exchange_rate': self.exchange_rate,
            'agreement_filename': self.agreement_filename,
            'budget_breakdown_filename': self.budget_breakdown_filename,
            'award_letter_filename': self.award_letter_filename,
            'pi_id': self.pi_id,
            'pi': {
                'name': self.pi.name if self.pi else 'N/A',
                'email': self.pi.email if self.pi else 'N/A'
            },
            'status': self.status,
            'project_progress_percentage': self.project_progress_percentage,
            'funder_id': self.funder_id,
            'health_score': self.health_score_rel.to_dict() if self.health_score_rel else None,
            # New fields
            'financial_reporting_frequency': self.financial_reporting_frequency,
            'progress_reporting_frequency': self.progress_reporting_frequency,
            'special_requirements': self.special_requirements,
            'ethical_approval_filename': self.ethical_approval_filename,
            'reporting_template_filename': self.reporting_template_filename,
            'indirect_cost_rate': self.indirect_cost_rate,
            'disbursed_funds': self.disbursed_funds,
            'available_disbursed_funds': (self.disbursed_funds or 0) - sum((cat.spent or 0.0) for cat in self.categories),
            'disbursement_type': self.disbursement_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'archive_hash': self.archive_hash,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            
            # Ethics Fields
            'ethics_required': self.ethics_required,
            'ethics_status': self.ethics_status,
            'ethics_expiry_date': self.ethics_expiry_date.isoformat() if self.ethics_expiry_date else None,
            'ethics_approval_number': self.ethics_approval_number,
            'ethics_certificate_filename': self.ethics_certificate_filename
        }

        if include_categories:
            data['categories'] = [category.to_dict() for category in self.categories]

        return data

    def can_release_tranche(self, tranche_number):
        """
        Gating logic for disbursement tranches.
        Returns True only if:
        1. ALL milestones linked to this tranche are COMPLETED.
        2. A corresponding financial report for the period exists and is APPROVED.
        """
        # 1. Check Milestones
        tranche_milestones = [m for m in self.milestones_list if m.triggers_tranche == tranche_number]
        if not tranche_milestones:
            # If no milestones are specifically tagged for this tranche, we might allow it 
            # if the previous tranche was released, but safety first: return False if none found.
            return False
            
        if not all(m.status == 'COMPLETED' for m in tranche_milestones):
            return False

        # 2. Check Financial Reports
        # Assuming period 1 maps to Tranche 1, etc.
        report = next((d for d in self.documents_list 
                      if d.doc_type == 'Financial Report' 
                      and not d.is_superseded 
                      and f"Tranche {tranche_number}" in d.file_name), None)
        
        # In a real system, we'd check an 'approval' status on the report document.
        # For now, if the document exists and is not superseded, we'll consider it "submitted/ready".
        return report is not None

class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    allocated = db.Column(db.Float, nullable=False)
    spent = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'name': self.name,
            'allocated': self.allocated,
            'spent': self.spent,
            'encumbered': self.encumbered or 0.0,
            'available': self.available
        }

    # Encumbrance for pending virements/purchases
    encumbered = db.Column(db.Float, default=0.0)

    @property
    def available(self):
        """Available balance after spent and encumbered amounts."""
        return (self.allocated or 0) - (self.spent or 0) - (self.encumbered or 0.0)


class ExpenseClaim(db.Model):
    __tablename__ = 'expense_claims'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(30), default='pending')  # pending, approved, rejected
    ageing_days = db.Column(db.Integer, default=0)
    
    # New fields for audit and detail
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    description = db.Column(db.Text)
    receipt_filename = db.Column(db.String(200))
    payment_method = db.Column(db.String(50))
    prior_approval_id = db.Column(db.Integer, db.ForeignKey('prior_approval_requests.id'))

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'submitted_by': self.submitted_by,
            'category': self.category,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'ageing_days': self.ageing_days,
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'description': self.description,
            'receipt_filename': self.receipt_filename,
            'payment_method': self.payment_method,
            'prior_approval_id': self.prior_approval_id,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense_claims.id'))
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    vendor = db.Column(db.String(120))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payment_reference = db.Column(db.String(100))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    paid_on = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'expense_id': self.expense_id,
            'grant_id': self.grant_id,
            'vendor': self.vendor,
            'amount': self.amount,
            'currency': self.currency,
            'payment_reference': self.payment_reference,
            'approved_by': self.approved_by,
            'paid_on': self.paid_on.isoformat() if self.paid_on else None
        }


class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), unique=True, nullable=False)
    buying_rate = db.Column(db.Float, nullable=False)
    selling_rate = db.Column(db.Float, nullable=False)
    buffer_spread = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'currency': self.currency,
            'buying_rate': self.buying_rate,
            'selling_rate': self.selling_rate,
            'buffer_spread': self.buffer_spread,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id')) # Optional for legacy, required for new flow
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    task_type = db.Column(db.String(50)) # e.g., 'Field Work', 'Lab Test'
    deadline = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    pay_rate_override = db.Column(db.Float)
    status = db.Column(db.String(20), default='PENDING') # PENDING, IN_PROGRESS, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grant = db.relationship('Grant', backref='tasks_list')
    assignee = db.relationship('User', backref='assigned_tasks_list')
    deliverable_submissions = db.relationship('DeliverableSubmission', backref='task', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'milestone_id': self.milestone_id,
            'assigned_to': self.assigned_to,
            'title': self.title,
            'task_type': self.task_type,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'estimated_hours': self.estimated_hours,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DeliverableSubmission(db.Model):
    __tablename__ = 'deliverable_submissions'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    file_path = db.Column(db.String(500))
    hours_worked = db.Column(db.Float)
    activity_notes = db.Column(db.Text)
    
    photo_path = db.Column(db.String(200)) # Legacy/Detailed
    document_paths = db.Column(db.Text)  # JSON string
    gps_coordinates = db.Column(db.String(50))
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_status = db.Column(db.String(20), default='pending') # pending, approved, revision_requested

    # Relationship back to task is handled via backref in Task model
    user = db.relationship('User', backref='deliverable_submissions_list')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Unknown',
            'file_path': self.file_path,
            'hours_worked': self.hours_worked,
            'activity_notes': self.activity_notes,
            'photo_path': self.photo_path,
            'document_paths': self.document_paths,
            'gps_coordinates': self.gps_coordinates,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'verification_status': self.verification_status
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class EffortCertification(db.Model):
    __tablename__ = 'effort_certifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    period_month = db.Column(db.Integer, nullable=False) # 1-12
    period_year = db.Column(db.Integer, nullable=False)
    certification_period = db.Column(db.String(20), nullable=False) # e.g. "2026-02"
    
    # The Data
    logged_hours = db.Column(db.Float) # Auto-calculated from DeliverableSubmission as reference
    certified_percentage = db.Column(db.Float) # MANUAL ENTRY by user (e.g., 37.5)
    
    # The Audit Trail
    signature_text = db.Column(db.String(100)) # Typed name for legal/audit purposes
    ip_address = db.Column(db.String(45))
    certified_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='PENDING') # PENDING, VERIFIED, REJECTED
    
    # "Ironclad" Rules tracking
    is_pi_certification = db.Column(db.Boolean, default=False)
    is_rsu_overridden = db.Column(db.Boolean, default=False)
    override_justification = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='effort_certifications_list')
    grant = db.relationship('Grant', backref='effort_certifications_list')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'grant_id': self.grant_id,
            'period_month': self.period_month,
            'period_year': self.period_year,
            'logged_hours': self.logged_hours,
            'certified_percentage': self.certified_percentage,
            'signature_text': self.signature_text,
            'ip_address': self.ip_address,
            'certified_at': self.certified_at.isoformat() if self.certified_at else None,
            'status': self.status,
            'is_pi_certification': self.is_pi_certification,
            'is_rsu_overridden': self.is_rsu_overridden,
            'override_justification': self.override_justification,
            'user_name': self.user.name if self.user else 'Unknown'
        }

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='NOT_STARTED') # NOT_STARTED, IN_PROGRESS, COMPLETED
    reporting_period = db.Column(db.String(50))
    completion_date = db.Column(db.DateTime)
    triggers_tranche = db.Column(db.Integer) # 1, 2, or 3
    funding_amount = db.Column(db.Float, default=0.0)
    release_status = db.Column(db.String(20), default='pending') # pending, released
    
    # Relationships
    grant = db.relationship('Grant', backref=db.backref('milestones_list', lazy=True, cascade='all, delete-orphan'))
    tasks = db.relationship('Task', backref='milestone_ptr', lazy=True, cascade="all, delete-orphan")
    deliverables = db.relationship('Deliverable', backref='milestone', lazy=True, cascade="all, delete-orphan")

    @property
    def progress_percentage(self):
        """Milestone progress: (completed tasks / total tasks) * 100"""
        if not self.tasks:
            return 0 if self.status != 'COMPLETED' else 100
        completed = sum(1 for t in self.tasks if t.status.upper() == 'COMPLETED')
        return int((completed / len(self.tasks)) * 100) if len(self.tasks) > 0 else 0

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'reporting_period': self.reporting_period,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'triggers_tranche': self.triggers_tranche,
            'funding_amount': self.funding_amount,
            'release_status': self.release_status,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'task_stats': {
                'total': len(self.tasks),
                'completed': sum(1 for t in self.tasks if t.status.upper() == 'COMPLETED')
            }
        }

class Deliverable(db.Model):
    __tablename__ = 'deliverables'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    deliverable_type = db.Column(db.String(50)) # 'Report', 'Dataset', 'Photo', 'Code'
    
    file_path = db.Column(db.String(500))
    external_url = db.Column(db.String(500)) # For DOI/GitHub links
    
    status = db.Column(db.String(20), default='PENDING') # PENDING, VERIFIED
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grant = db.relationship('Grant', backref='deliverables_list')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_deliverables')

    def to_dict(self):
        return {
            'id': self.id,
            'milestone_id': self.milestone_id,
            'grant_id': self.grant_id,
            'title': self.title,
            'deliverable_type': self.deliverable_type,
            'file_path': self.file_path,
            'external_url': self.external_url,
            'status': self.status,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }

class GrantTeam(db.Model):
    __tablename__ = 'grant_team'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False) # e.g., 'Co-PI', 'Co-Investigator', 'Research Assistant'
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active') # active, awaiting_prior_approval
    budget_authority = db.Column(db.Boolean, default=False) # Co-PI: can approve expenses/virements?

    # Establish relationships
    grant = db.relationship('Grant', backref=db.backref('team_members', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('grant_roles', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('grant_id', 'user_id', name='_grant_user_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'user_id': self.user_id,
            'role': self.role,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'status': self.status,
            'budget_authority': self.budget_authority,
            'is_co_pi': self.role == 'Co-PI',
            'name': self.user.name,
            'email': self.user.email,
            'system_role': self.user.role
        }

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.Integer, default=1)
    is_superseded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grant = db.relationship('Grant', backref=db.backref('documents_list', lazy=True, cascade='all, delete-orphan'))
    uploader = db.relationship('User', backref=db.backref('uploaded_documents', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'uploader_id': self.uploader_id,
            'uploader_name': self.uploader.name if self.uploader else 'Unknown',
            'uploader_role': self.uploader.role if self.uploader else 'N/A',
            'file_name': self.file_name,
            'file_path': self.file_path,
            'doc_type': self.doc_type,
            'version': self.version,
            'is_superseded': self.is_superseded,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# --- Rule Engine models 2.0 (Integrated Funder/Profile) ---

# --- Rule Engine Models 2.0 (Forensic Compliance Foundation) ---

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False) # e.g., "EXPENSE_LIMIT", "CATEGORY_MATCH"
    
    # Logic details: e.g., {"max_amount": 5000} or {"keywords": ["alcohol"]}
    logic_config = db.Column(db.JSON, nullable=False) 
    
    # Strictest Penalty Wins: BLOCK > PRIOR_APPROVAL > WARN > PASS
    outcome = db.Column(db.String(20), nullable=False) 
    
    priority_level = db.Column(db.Integer, default=3) # 1-High, 5-Low
    guidance_text = db.Column(db.Text) # PI-facing explanation
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rule_type': self.rule_type,
            'logic_config': self.logic_config,
            'outcome': self.outcome,
            'priority_level': self.priority_level,
            'guidance_text': self.guidance_text,
            'is_active': self.is_active
        }

# Association Table for FunderProfile <-> Rule
if 'funder_profile_rules' not in db.metadata.tables:
    funder_profile_rules = db.Table('funder_profile_rules',
        db.Column('profile_id', db.Integer, db.ForeignKey('funder_profiles.id'), primary_key=True),
        db.Column('rule_id', db.Integer, db.ForeignKey('rules.id'), primary_key=True)
    )
else:
    funder_profile_rules = db.metadata.tables['funder_profile_rules']

class FunderProfile(db.Model):
    __tablename__ = 'funder_profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # e.g., "USAID", "EU Horizon"
    funder_id = db.Column(db.String(50), unique=True) # Normalized ID for slug/API
    
    # Relationship to reusable rules
    rules = db.relationship('Rule', secondary=funder_profile_rules, backref='profiles')
    
    contact_info = db.Column(db.JSON)
    version_number = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @property
    def rules_config(self):
        """Returns JSON serialized rules for snapshots."""
        import json
        return json.dumps([r.to_dict() for r in self.rules])
    
    def to_dict(self, include_rules=False):
        data = {
            'id': self.id,
            'name': self.name,
            'funder_id': self.funder_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
        if include_rules:
            data['rules'] = [r.to_dict() for r in self.rules]
        return data

# Compatibility Alias for Compliance 1.0 logic
RuleProfile = FunderProfile

class RuleSnapshot(db.Model):
    """
    IMMUTABILITY: Snapshots the rules at the moment a grant is created.
    This ensures that changing a FunderProfile doesn't retroactively 
    affect existing grants (Audit proof).
    """
    __tablename__ = 'rule_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), unique=True)
    
    # Serialized blob of ALL rules linked to this grant at birth
    rules_json = db.Column(db.Text, nullable=False) 
    
    snapshot_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship - handled by Grant.rule_snapshot backref
    # (Removed to avoid double definition conflict)

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'rules': json.loads(self.rules_json) if self.rules_json else [],
            'snapshot_date': self.snapshot_date.isoformat()
        }

class RuleEvaluation(db.Model):
    """
    FORENSIC TRACEABILITY: Every compliance check is recorded.
    """
    __tablename__ = 'rule_evaluations'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    action_type = db.Column(db.String(50)) # EXPENSE, PERSONNEL, BUDGET, MILESTONE
    target_id = db.Column(db.Integer) # The ID of the expense/task being checked
    
    context_snapshot = db.Column(db.JSON) # The data at time of check (amount, desc, etc.)
    final_outcome = db.Column(db.String(20)) # BLOCK, WARN, PASS
    
    # Audit details
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    # Resolution (for PRIOR_APPROVAL or BLOCK overrides)
    resolution_outcome = db.Column(db.String(20)) # e.g., OVERRIDDEN, REJECTED
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    override_justification = db.Column(db.Text)
    override_cosigned_by = db.Column(db.Integer, db.ForeignKey('users.id')) # Dual sign-off
    
    # Relationships
    grant = db.relationship('Grant', backref='evaluations')
    evaluator = db.relationship('User', foreign_keys=[user_id], backref='rule_evaluations')

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'action_type': self.action_type,
            'target_id': self.target_id,
            'final_outcome': self.final_outcome,
            'evaluated_at': self.evaluated_at.isoformat(),
            'resolution_outcome': self.resolution_outcome,
            'override_justification': self.override_justification
        }

class ComplianceHealthScore(db.Model):
    __tablename__ = 'compliance_health_scores'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), unique=True)
    
    score = db.Column(db.Integer, default=100) # 100 = Perfect, 0 = Critical
    risk_level = db.Column(db.String(20)) # LOW, MEDIUM, HIGH, CRITICAL
    
    # Breakdown weights
    financial_risk = db.Column(db.Integer, default=0)
    operational_risk = db.Column(db.Integer, default=0)
    reporting_risk = db.Column(db.Integer, default=0)
    
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    grant_parent = db.relationship('Grant', foreign_keys=[grant_id], backref=db.backref('health_score_rel', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'score': self.score,
            'risk_level': self.risk_level,
            'financial_risk': self.financial_risk,
            'operational_risk': self.operational_risk,
            'reporting_risk': self.reporting_risk,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None
        }

class AuditTrail(db.Model):
    __tablename__ = 'audit_trail'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50)) # e.g., "OVERRIDE_BLOCK", "CHANGE_STATUS"
    entity_type = db.Column(db.String(50)) # e.g., "GRANT", "EXPENSE"
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON) # Old value vs New value
    is_override = db.Column(db.Boolean, default=False) # Critical flag
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    # Relationship
    user = db.relationship('User', backref='audit_trail_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'is_override': self.is_override,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class EthicsSuspensionPeriod(db.Model):
    __tablename__ = 'ethics_suspension_periods'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    suspended_at = db.Column(db.DateTime, default=datetime.utcnow)  # When suspension started
    suspension_reason = db.Column(db.String(255))                    # Why it was suspended
    reinstated_at = db.Column(db.DateTime, nullable=True)            # When RSU approved renewal
    reinstated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # RSU user who approved
    reinstatement_notes = db.Column(db.Text, nullable=True)          # RSU verification notes
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)

    grant = db.relationship('Grant', backref='suspension_periods')
    document = db.relationship('Document', backref='ethics_suspensions')
    reinstated_by_user = db.relationship('User', foreign_keys=[reinstated_by], backref='ethics_reinstatements')

    @property
    def duration_days(self):
        """Number of days the grant was suspended (None if still active)."""
        if self.suspended_at and self.reinstated_at:
            return (self.reinstated_at - self.suspended_at).days
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'suspended_at': self.suspended_at.isoformat() if self.suspended_at else None,
            'suspension_reason': self.suspension_reason,
            'reinstated_at': self.reinstated_at.isoformat() if self.reinstated_at else None,
            'reinstated_by': self.reinstated_by,
            'reinstated_by_name': self.reinstated_by_user.name if self.reinstated_by_user else None,
            'reinstatement_notes': self.reinstatement_notes,
            'duration_days': self.duration_days,
            'document_id': self.document_id
        }

class PriorApprovalRequest(db.Model):
    """
    WORKFLOW GATE: Triggered when a rule outcome is PRIOR_APPROVAL.
    """
    __tablename__ = 'prior_approval_requests'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    request_type = db.Column(db.String(50)) # EXPENSE, PERSONNEL, etc.
    target_id = db.Column(db.Integer) # The transaction ID
    rule_evaluation_id = db.Column(db.Integer, db.ForeignKey('rule_evaluations.id'))
    
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    justification = db.Column(db.Text)
    
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'request_type': self.request_type,
            'status': self.status,
            'justification': self.justification,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class RuleExemption(db.Model):
    """
    SPECIFIC OVERRIDES: Allows PI to bypass a specific rule for a specific grant.
    Must be approved by RSU.
    """
    __tablename__ = 'rule_exemptions'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('rules.id'), nullable=False)
    
    justification = db.Column(db.Text, nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'rule_id': self.rule_id,
            'is_active': self.is_active,
            'justification': self.justification
        }

# --- Budget Virement & Encumbrance ---
class BudgetVirement(db.Model):
    __tablename__ = 'budget_virements'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    from_category_id = db.Column(db.Integer, db.ForeignKey('budget_categories.id'), nullable=False)
    to_category_id = db.Column(db.Integer, db.ForeignKey('budget_categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    justification = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected, cancelled
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    # Relationships
    grant_ref = db.relationship('Grant', foreign_keys=[grant_id], backref='virements_history')
    from_category = db.relationship('BudgetCategory', foreign_keys=[from_category_id], backref='virements_out')
    to_category = db.relationship('BudgetCategory', foreign_keys=[to_category_id], backref='virements_in')
    creator = db.relationship('User', foreign_keys=[created_by_id], backref='virements_requested')
    workflow = db.relationship('ApprovalWorkflow', foreign_keys=[workflow_id], backref='virement_target')

    def to_dict(self):
        latest_comment = None
        if self.workflow_id:
            # Get the most recent comment from approval logs
            last_log = ApprovalLog.query.filter_by(workflow_id=self.workflow_id).order_by(ApprovalLog.timestamp.desc()).first()
            if last_log:
                latest_comment = last_log.comment

        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'from_category_id': self.from_category_id,
            'to_category_id': self.to_category_id,
            'from_category_name': self.from_category.name if self.from_category else 'Unknown',
            'to_category_name': self.to_category.name if self.to_category else 'Unknown',
            'amount': self.amount,
            'justification': self.justification,
            'status': self.status,
            'workflow_id': self.workflow_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'requester_name': self.creator.name if self.creator else 'Unknown',
            'resolver_comment': latest_comment
        }

# --- Multi-Stage Approval Engine ---
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g., 'TRANCHE_READY', 'MILESTONE_COMPLETED'
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.JSON, nullable=True) # Extra context (grant_id, etc.)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ApprovalWorkflow(db.Model):
    __tablename__ = 'approval_workflows'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=True) # Linked grant context
    item_type = db.Column(db.String(50), nullable=False) # EXPENSE, VIREMENT, PERSONNEL
    item_id = db.Column(db.Integer, nullable=False)
    current_step_order = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='in_progress') # in_progress, completed, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    grant = db.relationship('Grant', backref='workflows')

class ApprovalStep(db.Model):
    __tablename__ = 'approval_steps'
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    role_required = db.Column(db.String(20), nullable=False) # PI, FINANCE, RSU, DEPT_HEAD
    order = db.Column(db.Integer, nullable=False)
    is_parallel = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending') # pending, active, approved, rejected
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)

class ApprovalLog(db.Model):
    __tablename__ = 'approval_logs'
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False) # APPROVE, REJECT, COMMENT
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- Risk Monitoring (Legacy Support) ---
class ComplianceMonitoring(db.Model):
    __tablename__ = 'compliance_monitoring'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    overall_score = db.Column(db.Integer, default=100)
    risk_level = db.Column(db.String(20), default='low') # low, medium, high, critical
    budget_compliance_score = db.Column(db.Integer, default=100)
    reporting_compliance_score = db.Column(db.Integer, default=100)
    task_completion_score = db.Column(db.Integer, default=100)
    risk_factors = db.Column(db.Text) # JSON string of factors
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    grant = db.relationship('Grant', backref=db.backref('compliance_record', uselist=False))


class Tranche(db.Model):
    __tablename__ = 'tranches'
    id = db.Column(db.Integer, primary_key = True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable = False)
    
    # Basic Info
    tranche_number = db.Column(db.Integer) # 1, 2, 3...
    amount = db.Column(db.Float, nullable = False)
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.String(200)) # e.g., "Initial Mobilization"
    expected_date = db.Column(db.Date, nullable = False)
    
    # NEW: Flexible Triggers
    trigger_type = db.Column(db.String(20), default='milestone') # 'milestone', 'report', 'date', 'manual'
    triggering_milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    required_report_type = db.Column(db.String(50), nullable=True) # 'financial', 'progress', 'technical'
    trigger_date = db.Column(db.Date, nullable=True) # For date-based triggers
    
    # Status & Release
    status = db.Column(db.String(20), default = 'pending') # pending, ready, released, suspended, archived
    actual_received_date = db.Column(db.Date)
    released_at = db.Column(db.DateTime)
    released_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # NEW: Amendment Tracking
    version = db.Column(db.Integer, default=1)
    parent_tranche_id = db.Column(db.Integer, db.ForeignKey('tranches.id'), nullable=True)
    amendment_reason = db.Column(db.Text, nullable=True)
    amendment_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amendment_approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    updated_at = db.Column(db.DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)

    # Relationships
    grant = db.relationship('Grant', backref = db.backref('tranches', lazy = True, cascade = 'all, delete-orphan'))
    triggering_milestone = db.relationship('Milestone', foreign_keys=[triggering_milestone_id], backref='triggered_tranches')
    released_by_user = db.relationship('User', foreign_keys=[released_by], backref='released_tranches')
    amendment_approved_by_user = db.relationship('User', foreign_keys=[amendment_approved_by], backref='approved_amendments')
    child_tranches = db.relationship('Tranche', backref=db.backref('parent_tranche', remote_side=[id]))

    def to_dict(self, include_amendments=False):
        result = {
            'id': self.id,
            'grant_id': self.grant_id,
            'amount': self.amount,
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'status': self.status,
            'actual_received_date': self.actual_received_date.isoformat() if self.actual_received_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add new fields if they exist (for backward compatibility)
        if hasattr(self, 'tranche_number'):
            result['tranche_number'] = self.tranche_number
        else:
            # Fallback: generate tranche_number from order
            if hasattr(self, 'id'):
                result['tranche_number'] = self.id
            else:
                result['tranche_number'] = 1
        
        if hasattr(self, 'currency'):
            result['currency'] = self.currency
        return result

class NoCostExtension(db.Model):
    """
    TIMELINE GATE: Formal request to extend project end date.
    """
    __tablename__ = 'no_cost_extensions'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    current_end_date = db.Column(db.Date, nullable=False)
    requested_end_date = db.Column(db.Date, nullable=False)
    justification = db.Column(db.Text, nullable=False)
    
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id')) # Funder letter
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    
    resolver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    resolver_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grant = db.relationship('Grant', backref='extensions')
    requester = db.relationship('User', foreign_keys=[requester_id], backref='extensions_requested')
    resolver = db.relationship('User', foreign_keys=[resolver_id], backref='extensions_resolved')
    document = db.relationship('Document', backref='extension_evidence')

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'requester_id': self.requester_id,
            'requester_name': self.requester.name if self.requester else 'Unknown',
            'current_end_date': self.current_end_date.isoformat() if self.current_end_date else None,
            'requested_end_date': self.requested_end_date.isoformat() if self.requested_end_date else None,
            'justification': self.justification,
            'status': self.status,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolver_notes': self.resolver_notes,
            'document_id': self.document_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        # Add trigger information if available
        if hasattr(self, 'trigger_type'):
            result['trigger_type'] = self.trigger_type
        else:
            result['trigger_type'] = 'milestone'
            
        if hasattr(self, 'triggering_milestone_id'):
            result['triggering_milestone_id'] = self.triggering_milestone_id
        else:
            result['triggering_milestone_id'] = None
            
        if hasattr(self, 'required_report_type'):
            result['required_report_type'] = self.required_report_type
        else:
            result['required_report_type'] = None
            
        if hasattr(self, 'trigger_date'):
            result['trigger_date'] = self.trigger_date.isoformat() if self.trigger_date else None
        else:
            result['trigger_date'] = None
        
        # Add release information if available
        if hasattr(self, 'released_at'):
            result['released_at'] = self.released_at.isoformat() if self.released_at else None
        else:
            result['released_at'] = None
            
        if hasattr(self, 'released_by'):
            result['released_by'] = self.released_by
        else:
            result['released_by'] = None
        
        # Add amendment tracking if available
        if hasattr(self, 'version'):
            result['version'] = self.version
        else:
            result['version'] = 1
            
        if hasattr(self, 'parent_tranche_id'):
            result['parent_tranche_id'] = self.parent_tranche_id
        else:
            result['parent_tranche_id'] = None
            
        if hasattr(self, 'amendment_reason'):
            result['amendment_reason'] = self.amendment_reason
        else:
            result['amendment_reason'] = None
            
        if hasattr(self, 'amendment_approved_by'):
            result['amendment_approved_by'] = self.amendment_approved_by
        else:
            result['amendment_approved_by'] = None
            
        if hasattr(self, 'amendment_approved_at'):
            result['amendment_approved_at'] = self.amendment_approved_at.isoformat() if self.amendment_approved_at else None
        else:
            result['amendment_approved_at'] = None
            
        if hasattr(self, 'updated_at'):
            result['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        else:
            result['updated_at'] = result['created_at']
        
        # Add related object data (with safety checks)
        try:
            if hasattr(self, 'triggering_milestone') and self.triggering_milestone:
                result['triggering_milestone'] = {
                    'id': self.triggering_milestone.id,
                    'title': self.triggering_milestone.title,
                    'status': self.triggering_milestone.status
                }
        except:
            result['triggering_milestone'] = None
        
        try:
            if hasattr(self, 'released_by_user') and self.released_by_user:
                result['released_by_user'] = {
                    'id': self.released_by_user.id,
                    'name': self.released_by_user.name
                }
        except:
            result['released_by_user'] = None
        
        # Add amendment history if requested
        if include_amendments:
            try:
                # Import TrancheAmendment locally to avoid circular imports
                from models import TrancheAmendment
                result['amendment_history'] = [amendment.to_dict() for amendment in TrancheAmendment.query.filter_by(tranche_id=self.id).all()]
            except ImportError:
                # TrancheAmendment model not available yet
                result['amendment_history'] = []
            except Exception as e:
                # Any other error with amendment history
                result['amendment_history'] = []
                print(f"Warning: Could not load amendment history: {e}")
        
        return result

class TrancheAmendment(db.Model):
    __tablename__ = 'tranche_amendments'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'))
    tranche_id = db.Column(db.Integer, db.ForeignKey('tranches.id'))
    
    # Amendment Details
    amendment_type = db.Column(db.String(20)) # 'amount', 'trigger', 'date', 'delete'
    old_value = db.Column(db.Text) # JSON of old values
    new_value = db.Column(db.Text) # JSON of new values
    reason = db.Column(db.Text, nullable=False)
    
    # Supporting Documents
    supporting_docs = db.Column(db.Text) # JSON array of file paths
    
    # Approval Workflow
    status = db.Column(db.String(20), default='pending') # 'pending', 'approved', 'rejected'
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grant = db.relationship('Grant', backref='tranche_amendments')
    tranche = db.relationship('Tranche', backref='amendments')
    requested_by_user = db.relationship('User', foreign_keys=[requested_by], backref='requested_amendments')
    approved_by_user = db.relationship('User', foreign_keys=[approved_by], backref='approved_tranche_amendments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'tranche_id': self.tranche_id,
            'amendment_type': self.amendment_type,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'reason': self.reason,
            'supporting_docs': self.supporting_docs,
            'status': self.status,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Add user info
            'requested_by_user': {
                'id': self.requested_by_user.id,
                'name': self.requested_by_user.name
            } if self.requested_by_user else None,
            'approved_by_user': {
                'id': self.approved_by_user.id,
                'name': self.approved_by_user.name
            } if self.approved_by_user else None
        }

# --- NCE, BURN RATE & FORECASTING MODELS ---

class GrantAmendment(db.Model):
    __tablename__ = 'grant_amendments'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    
    # Amendment Details
    amendment_type = db.Column(db.String(20), default='NCE')  # NCE, BUDGET_SHIFT, SCOPE_CHANGE
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # NCE Specific Fields
    current_end_date = db.Column(db.Date)
    requested_new_end_date = db.Column(db.Date)
    extension_days = db.Column(db.Integer)  # Calculated automatically
    
    # Budget Amendment Fields (for future use)
    old_budget = db.Column(db.Float)
    new_budget = db.Column(db.Float)
    budget_change = db.Column(db.Float)
    
    # Workflow & Approval
    status = db.Column(db.String(20), default='PENDING')  # PENDING, APPROVED, REJECTED, WITHDRAWN
    priority = db.Column(db.String(10), default='NORMAL')  # LOW, NORMAL, HIGH, URGENT
    
    # Justification & Documentation
    justification = db.Column(db.Text, nullable=False)
    supporting_docs = db.Column(db.JSON)  # File references, URLs, document IDs
    funder_approval_ref = db.Column(db.String(100))  # Funder reference number
    funder_contact_email = db.Column(db.String(100))
    
    # Audit Trail
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grant = db.relationship('Grant', backref=db.backref('amendments', lazy=True, cascade='all, delete-orphan'))
    requester = db.relationship('User', foreign_keys=[requested_by], backref='nce_requests')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='nce_approvals')
    rejecter = db.relationship('User', foreign_keys=[rejected_by], backref='nce_rejections')
    
    def __repr__(self):
        return f'<GrantAmendment {self.id}: {self.amendment_type} for Grant {self.grant_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'amendment_type': self.amendment_type,
            'title': self.title,
            'description': self.description,
            'current_end_date': self.current_end_date.isoformat() if self.current_end_date else None,
            'requested_new_end_date': self.requested_new_end_date.isoformat() if self.requested_new_end_date else None,
            'extension_days': self.extension_days,
            'status': self.status,
            'priority': self.priority,
            'justification': self.justification,
            'supporting_docs': self.supporting_docs,
            'funder_approval_ref': self.funder_approval_ref,
            'funder_contact_email': self.funder_contact_email,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'rejected_by': self.rejected_by,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GrantFinancialMetrics(db.Model):
    __tablename__ = 'grant_financial_metrics'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False, unique=True)
    
    # Burn Rate Metrics
    time_elapsed_percentage = db.Column(db.Float, default=0.0)
    budget_spent_percentage = db.Column(db.Float, default=0.0)
    burn_rate_variance = db.Column(db.Float, default=0.0)  # Spent% - Time%
    burn_rate_status = db.Column(db.String(20), default='ON_TRACK')  # ON_TRACK, OVER_SPENDING, UNDER_SPENDING
    
    # Forecasting Metrics
    projected_final_spend = db.Column(db.Float, default=0.0)
    projected_remaining_balance = db.Column(db.Float, default=0.0)
    forecast_status = db.Column(db.String(20), default='HEALTHY')  # HEALTHY, TIGHT, DEFICIT
    
    # Committed Costs (Encumbrances)
    pending_expenses_total = db.Column(db.Float, default=0.0)
    approved_purchase_orders_total = db.Column(db.Float, default=0.0)
    recurring_monthly_costs = db.Column(db.Float, default=0.0)
    
    # Risk Indicators
    risk_score = db.Column(db.Float, default=0.0)  # 0-100 scale
    risk_factors = db.Column(db.JSON)  # Array of risk factor strings
    
    # Alert Thresholds
    last_alert_sent = db.Column(db.DateTime)
    alert_frequency = db.Column(db.String(20), default='WEEKLY')  # DAILY, WEEKLY, MONTHLY
    
    # Timestamps
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grant = db.relationship('Grant', backref=db.backref('financial_metrics', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'time_elapsed_percentage': round(self.time_elapsed_percentage, 1),
            'budget_spent_percentage': round(self.budget_spent_percentage, 1),
            'burn_rate_variance': round(self.burn_rate_variance, 1),
            'burn_rate_status': self.burn_rate_status,
            'projected_final_spend': round(self.projected_final_spend, 2),
            'projected_remaining_balance': round(self.projected_remaining_balance, 2),
            'forecast_status': self.forecast_status,
            'pending_expenses_total': round(self.pending_expenses_total, 2),
            'approved_purchase_orders_total': round(self.approved_purchase_orders_total, 2),
            'recurring_monthly_costs': round(self.recurring_monthly_costs, 2),
            'risk_score': round(self.risk_score, 1),
            'risk_factors': self.risk_factors or [],
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None
        }

# --- ASSET & EQUIPMENT MANAGEMENT MODELS ---

class Asset(db.Model):
    __tablename__ = 'assets'
    
    # Primary Identification
    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(50), unique=True)  # Internal ID
    serial_number = db.Column(db.String(100))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'Vehicle', 'IT', 'Lab Equipment'
    
    # Grant Context
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    grant = db.relationship('Grant', backref='assets')
    
    # Source & Ownership
    source_type = db.Column(db.String(20), nullable=False)  # 'PURCHASED', 'LENDED', 'UNIVERSITY_OWNED'
    owner_name = db.Column(db.String(200))  # "MUBAS", "Ministry of Health", "USAID"
    lending_agreement = db.Column(db.Text)  # Details of lending arrangement
    
    # Financial Information
    purchase_cost = db.Column(db.Float, default=0.0)
    linked_expense_id = db.Column(db.Integer, db.ForeignKey('expense_claims.id'))
    rental_fee_total = db.Column(db.Float, default=0.0)
    depreciation_value = db.Column(db.Float, default=0.0)
    
    # Lifecycle Management
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, IN_REPAIR, LOST, RETURNED, TRANSFERRED, DISPOSED
    custodian_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    custodian = db.relationship('User', foreign_keys=[custodian_user_id])
    assigned_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    assigned_task = db.relationship('Task')
    
    # Important Dates
    acquisition_date = db.Column(db.Date)
    expected_return_date = db.Column(db.Date)  # Critical for LENDED items
    actual_return_date = db.Column(db.Date)
    last_maintenance_date = db.Column(db.Date)
    next_maintenance_date = db.Column(db.Date)
    
    # Disposition (Closeout)
    disposition_method = db.Column(db.String(50))  # 'Transfer to Uni', 'Return to Donor', 'Sold', 'Destroyed'
    disposition_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    disposition_approver = db.relationship('User', foreign_keys=[disposition_approved_by])
    disposition_date = db.Column(db.Date)
    disposition_notes = db.Column(db.Text)
    
    # Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', foreign_keys=[created_by_user_id])
    
    # Documents & Attachments
    supporting_documents = db.Column(db.JSON)  # Receipts, agreements, photos
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_tag': self.asset_tag,
            'serial_number': self.serial_number,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'grant_id': self.grant_id,
            'source_type': self.source_type,
            'owner_name': self.owner_name,
            'purchase_cost': self.purchase_cost,
            'rental_fee_total': self.rental_fee_total,
            'status': self.status,
            'custodian': self.custodian.to_dict() if self.custodian else None,
            'assigned_task': self.assigned_task.to_dict() if self.assigned_task else None,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'expected_return_date': self.expected_return_date.isoformat() if self.expected_return_date else None,
            'actual_return_date': self.actual_return_date.isoformat() if self.actual_return_date else None,
            'disposition_method': self.disposition_method,
            'supporting_documents': self.supporting_documents,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AssetMaintenance(db.Model):
    __tablename__ = 'asset_maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    asset = db.relationship('Asset', backref='maintenance_records')
    
    maintenance_type = db.Column(db.String(50))  # 'Scheduled', 'Repair', 'Inspection'
    description = db.Column(db.Text)
    cost = db.Column(db.Float, default=0.0)
    performed_by = db.Column(db.String(200))
    performed_date = db.Column(db.Date)
    next_due_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'maintenance_type': self.maintenance_type,
            'description': self.description,
            'cost': self.cost,
            'performed_by': self.performed_by,
            'performed_date': self.performed_date.isoformat() if self.performed_date else None,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AssetTransfer(db.Model):
    __tablename__ = 'asset_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    asset = db.relationship('Asset', backref='transfer_records')
    
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    from_user = db.relationship('User', foreign_keys=[from_user_id])
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to_user = db.relationship('User', foreign_keys=[to_user_id])
    
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'from_user': self.from_user.to_dict() if self.from_user else None,
            'to_user': self.to_user.to_dict() if self.to_user else None,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None,
            'reason': self.reason,
            'approver': self.approver.to_dict() if self.approver else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AssetAssignment(db.Model):
    """Junction table to track which assets are needed/used for a specific task"""
    __tablename__ = 'asset_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # Assignment status workflow
    status = db.Column(db.String(20), default='REQUESTED')  # REQUESTED -> ASSIGNED -> RETURNED
    
    # Timestamps for full audit trail
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    
    # Accountability tracking
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pickup_confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    return_confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Evidence & verification
    pickup_evidence_doc = db.Column(db.String(255))  # Photo/QR scan
    return_evidence_doc = db.Column(db.String(255))   # Photo/handover proof
    notes = db.Column(db.Text)
    
    # Relationships
    asset = db.relationship('Asset', backref='assignments')
    task = db.relationship('Task', backref='asset_assignments')
    assigned_user = db.relationship('User', foreign_keys=[assigned_to_user_id])
    pickup_confirmer = db.relationship('User', foreign_keys=[pickup_confirmed_by])
    return_confirmer = db.relationship('User', foreign_keys=[return_confirmed_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'asset_id': self.asset_id,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'returned_at': self.returned_at.isoformat() if self.returned_at else None,
            'assigned_to_user_id': self.assigned_to_user_id,
            'pickup_confirmed_by': self.pickup_confirmed_by,
            'return_confirmed_by': self.return_confirmed_by,
            'pickup_evidence_doc': self.pickup_evidence_doc,
            'return_evidence_doc': self.return_evidence_doc,
            'notes': self.notes,
            'asset': self.asset.to_dict() if self.asset else None,
            'task': self.task.to_dict() if self.task else None,
            'assigned_user': self.assigned_user.to_dict() if self.assigned_user else None,
            'pickup_confirmer': self.pickup_confirmer.to_dict() if self.pickup_confirmer else None,
            'return_confirmer': self.return_confirmer.to_dict() if self.return_confirmer else None
        }

class MilestoneKPI(db.Model):
    """Milestone-level KPI allocation - links milestone to grant KPI with specific target"""
    __tablename__ = 'milestone_kpis'
    
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    grant_kpi_id = db.Column(db.Integer, db.ForeignKey('grant_kpis.id'), nullable=False)
    
    # Milestone-specific target (portion of grant-wide target)
    milestone_target = db.Column(db.Float, nullable=False)
    
    # Results (Filled at completion)
    actual_value = db.Column(db.Float, nullable=True)
    achievement_pct = db.Column(db.Float, nullable=True)  # Auto-calculated
    evidence_link = db.Column(db.String(255))             # Link to Deliverable ID
    
    status = db.Column(db.String(20), default='PENDING')  # PENDING, ACHIEVED, PARTIAL, MISSED
    
    # Relationships
    milestone = db.relationship('Milestone', backref='milestone_kpis')
    
    # Computed properties - delegate to grant KPI
    @property
    def kpi_name(self):
        return self.grant_kpi.name
    
    @property
    def kpi_description(self):
        return self.grant_kpi.description
    
    @property
    def kpi_unit(self):
        return self.grant_kpi.unit
    
    @property
    def kpi_category(self):
        return self.grant_kpi.category
    
    def calculate_achievement(self):
        """Calculate achievement percentage and status"""
        if self.actual_value is not None and self.milestone_target > 0:
            self.achievement_pct = (self.actual_value / self.milestone_target) * 100
            if self.achievement_pct >= 100:
                self.status = 'ACHIEVED'
            elif self.achievement_pct > 0:
                self.status = 'PARTIAL'
            else:
                self.status = 'MISSED'
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'milestone_id': self.milestone_id,
            'grant_kpi_id': self.grant_kpi_id,
            'kpi_name': self.kpi_name,
            'kpi_description': self.kpi_description,
            'kpi_unit': self.kpi_unit,
            'kpi_category': self.kpi_category,
            'milestone_target': self.milestone_target,
            'actual_value': self.actual_value,
            'achievement_pct': self.achievement_pct,
            'evidence_link': self.evidence_link,
            'status': self.status
        }

class MilestoneTemplate(db.Model):
    """Standard templates for common milestone types with asset and KPI configurations"""
    __tablename__ = 'milestone_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)     # e.g., "Standard Field Work"
    
    # JSON storing list of required asset categories/IDs and KPI configurations
    config_json = db.Column(db.JSON, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'config_json': self.config_json,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GrantKPI(db.Model):
    """Grant-level Key Performance Indicators - Master KPI list defined at grant initialization"""
    __tablename__ = 'grant_kpis'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    
    # KPI Definition
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(50))  # count, percentage, currency, hours, papers, students, people, etc.
    category = db.Column(db.String(50))  # research, training, infrastructure, community, financial
    
    # Grant-wide targets
    grant_wide_target = db.Column(db.Float, nullable=False)
    baseline_value = db.Column(db.Float, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    grant = db.relationship('Grant', backref=db.backref('grant_kpis', lazy=True, cascade='all, delete-orphan'))
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    milestone_kpis = db.relationship('MilestoneKPI', backref='grant_kpi', lazy=True, cascade='all, delete-orphan')
    
    # Computed properties
    @property
    def total_actual(self):
        """Sum of all actual values from milestone allocations"""
        return sum(kpi.actual_value or 0 for kpi in self.milestone_kpis)
    
    @property
    def achievement_pct(self):
        """Overall achievement percentage across all milestones"""
        if self.grant_wide_target == 0:
            return 0
        return (self.total_actual / self.grant_wide_target) * 100
    
    @property
    def status(self):
        """Overall KPI status"""
        achievement = self.achievement_pct
        if achievement >= 100:
            return 'ACHIEVED'
        elif achievement >= 50:
            return 'PARTIAL'
        elif achievement > 0:
            return 'IN_PROGRESS'
        else:
            return 'PENDING'
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'category': self.category,
            'grant_wide_target': self.grant_wide_target,
            'baseline_value': self.baseline_value,
            'total_actual': self.total_actual,
            'achievement_pct': self.achievement_pct,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CalendarEvent(db.Model):
    __tablename__ = 'calendar_events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    event_type = db.Column(db.String(50), default='PERSONAL') # PERSONAL, GRANT, BROADCAST, SYSTEM, FINANCE
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'))
    target_role = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', backref='my_calendar_events')
    grant = db.relationship('Grant', backref='calendar_events')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'event_type': self.event_type,
            'user_id': self.user_id,
            'grant_id': self.grant_id,
            'target_role': self.target_role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
