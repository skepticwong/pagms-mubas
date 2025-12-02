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
    funder = db.Column(db.String(100), nullable=False)
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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    categories = db.relationship(
        'BudgetCategory', backref='grant', lazy=True, cascade='all, delete-orphan'
    )
    
    def to_dict(self, include_categories: bool = False):
        """Convert Grant object to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'title': self.title,
            'funder': self.funder,
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
            # New fields
            'financial_reporting_frequency': self.financial_reporting_frequency,
            'progress_reporting_frequency': self.progress_reporting_frequency,
            'special_requirements': self.special_requirements,
            'ethical_approval_filename': self.ethical_approval_filename,
            
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

        if include_categories:
            data['categories'] = [category.to_dict() for category in self.categories]

        return data

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
            'spent': self.spent
        }


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
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    estimated_hours = db.Column(db.Float)
    pay_rate_override = db.Column(db.Float)
    status = db.Column(db.String(20), default='assigned')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    grant = db.relationship('Grant', backref='tasks')
    assignee = db.relationship('User', backref='assigned_tasks')

    def to_dict(self):
        """Convert Task object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'assigned_to': self.assigned_to,
            'title': self.title,
            'task_type': self.task_type,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'estimated_hours': self.estimated_hours,
            'pay_rate_override': self.pay_rate_override,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EvidenceSubmission(db.Model):
    __tablename__ = 'evidence_submissions'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    hours_worked = db.Column(db.Float, nullable=False)
    photo_path = db.Column(db.String(200))
    document_paths = db.Column(db.Text)  # JSON string
    activity_notes = db.Column(db.Text)
    exif_timestamp = db.Column(db.String(50))
    gps_coordinates = db.Column(db.String(50))
    is_photo_duplicate = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    # reporting_period values: 'q1_year1', 'annual_1', 'final', etc.
    reporting_period = db.Column(db.String(50))
    status = db.Column(db.String(20), default='not_started') # not_started, in_progress, completed
    completion_date = db.Column(db.Date)
    
    # Use relationship to access grant
    grant = db.relationship('Grant', backref=db.backref('milestones', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'reporting_period': self.reporting_period,
            'status': self.status,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None
        }

class GrantTeam(db.Model):
    __tablename__ = 'grant_team'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False) # e.g., 'Co-Investigator', 'Research Assistant'
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

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
            'name': self.user.name,
            'email': self.user.email
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