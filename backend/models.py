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
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_budget = db.Column(db.Float, nullable=False)
    pi_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert Grant object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'funder': self.funder,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'total_budget': self.total_budget,
            'pi_id': self.pi_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    allocated = db.Column(db.Float, nullable=False)

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