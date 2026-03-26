import sys
print("Test script started")
import os
import unittest
from datetime import date, timedelta

# Add parent directory to sys.path to import app and models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Milestone, Task, Grant, User, BudgetCategory, EffortCertification
from services.milestone_service import MilestoneService
from services.task_service import TaskService
import json

class TestMilestoneEnhancements(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.pi = User(name='Dr. PI', email='pi@test.com', role='PI')
        self.rsu = User(name='RSU Admin', email='rsu@test.com', role='RSU')
        db.session.add_all([self.pi, self.rsu])
        db.session.commit()
        
        # Create test grant
        self.grant = Grant(
            title='Test Grant',
            grant_code='TG001',
            pi_id=self.pi.id,
            total_budget=10000,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            status='active'
        )
        db.session.add(self.grant)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_manual_completion_hard_block(self):
        """Test that a milestone cannot be completed manually if tasks are pending."""
        m = Milestone(
            grant_id=self.grant.id,
            title='Phase 1',
            due_date=date.today() + timedelta(days=30),
            status='in_progress'
        )
        db.session.add(m)
        db.session.commit()
        
        t = Task(
            grant_id=self.grant.id,
            assigned_to=self.pi.id,
            title='Task A',
            status='assigned',
            milestone_id=m.id,
            deadline=date.today(),
            task_type='Administrative'
        )
        db.session.add(t)
        db.session.commit()
        
        # Try to mark milestone as completed
        with self.assertRaises(ValueError) as cm:
            MilestoneService.update_status(m.id, 'completed', self.pi.id)
        
        self.assertIn("Cannot complete milestone: 1 task(s)", str(cm.exception))
        self.assertEqual(m.status, 'in_progress')

    def test_auto_transition_to_ready(self):
        """Test that a milestone transitions to ready_for_completion when last task is approved."""
        m = Milestone(
            grant_id=self.grant.id,
            title='Phase 1',
            due_date=date.today() + timedelta(days=30),
            status='in_progress'
        )
        db.session.add(m)
        
        t = Task(
            grant_id=self.grant.id,
            assigned_to=self.pi.id,
            title='Task A',
            status='assigned',
            milestone_id=m.id,
            deadline=date.today(),
            task_type='Administrative'
        )
        db.session.add(t)
        db.session.commit()
        
        # Mock Deliverables Submission
        from models import DeliverablesSubmission
        sub = DeliverablesSubmission(
            task_id=t.id,
            submitted_by=self.pi.id,
            verification_status='pending',
            hours_worked=5.0
        )
        db.session.add(sub)
        db.session.commit()
        
        # Approve task
        TaskService.verify_deliverables(sub.id, 'approved', self.pi.id)
        
        # Check milestone status
        m_refreshed = Milestone.query.get(m.id)
        self.assertEqual(m_refreshed.status, 'ready_for_completion')

    def test_waiver_override(self):
        """Test that a waiver allows completion even with pending tasks."""
        m = Milestone(
            grant_id=self.grant.id,
            title='Phase 1',
            due_date=date.today() + timedelta(days=30),
            status='in_progress',
            waiver_approved=True # Mocked approval
        )
        db.session.add(m)
        
        t = Task(
            grant_id=self.grant.id,
            assigned_to=self.pi.id,
            title='Task A',
            status='assigned',
            milestone_id=m.id,
            deadline=date.today(),
            task_type='Administrative'
        )
        db.session.add(t)
        db.session.commit()
        
        # Should NOT raise error because waiver is approved
        res = MilestoneService.update_status(m.id, 'completed', self.pi.id)
        self.assertEqual(res['status'], 'completed')

if __name__ == '__main__':
    unittest.main()
