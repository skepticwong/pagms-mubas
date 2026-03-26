# test_risk_monitor.py
import unittest
import os
from datetime import datetime, timedelta

# Set TESTING environment variable before importing app to prevent schedulers
os.environ['TESTING'] = 'true'

from app import create_app
from models import db, Grant, User, Milestone, ComplianceMonitoring, Task

class TestRiskMonitor(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        # Ensure TESTING is actually in the config
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.pi = User(name='Test PI', email='pi@test.com', role='PI')
        self.rsu = User(name='Test RSU', email='rsu@test.com', role='RSU')
        db.session.add(self.pi)
        db.session.add(self.rsu)
        db.session.commit()
        
        # Create test grant
        self.grant = Grant(
            grant_code='G-RISK-001',
            title='Risk Test Grant',
            pi_id=self.pi.id,
            total_budget=10000,
            start_date=datetime.utcnow().date() - timedelta(days=30),
            end_date=datetime.utcnow().date() + timedelta(days=30)
        )
        db.session.add(self.grant)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_risk_score_with_waivers(self):
        """Verify that approved waivers reduce the compliance score"""
        # Baseline score (no waivers, all tasks done)
        monitoring = ComplianceMonitoring.calculate_compliance_score(self.grant.id)
        baseline_score = monitoring.overall_score
        
        # Add tasks and milestones with waivers
        m1 = Milestone(grant_id=self.grant.id, title='M1', due_date=datetime.utcnow().date(), status='completed', waiver_approved=True)
        db.session.add(m1)
        db.session.commit()
        
        # Recalculate
        monitoring = ComplianceMonitoring.calculate_compliance_score(self.grant.id)
        score_after_waiver = monitoring.overall_score
        
        self.assertLess(score_after_waiver, baseline_score)
        self.assertIn("effort certification waivers utilized", monitoring.risk_factors)

    def test_risk_score_with_buffer_inactivity(self):
        """Verify that stale milestones in ready_for_completion reduce the score"""
        monitoring = ComplianceMonitoring.calculate_compliance_score(self.grant.id)
        baseline_score = monitoring.overall_score
        
        # Add a stale milestone
        stale_date = datetime.utcnow() - timedelta(days=15)
        m_stale = Milestone(
            grant_id=self.grant.id, 
            title='Stale Milestone', 
            status='ready_for_completion',
            updated_at=stale_date
        )
        db.session.add(m_stale)
        # Manually force updated_at because of onupdate
        db.session.commit()
        m_stale.updated_at = stale_date
        db.session.commit()
        
        # Recalculate
        monitoring = ComplianceMonitoring.calculate_compliance_score(self.grant.id)
        score_after_stale = monitoring.overall_score
        
        self.assertLess(score_after_stale, baseline_score)
        self.assertIn("milestones awaiting PI confirmation", monitoring.risk_factors)

if __name__ == '__main__':
    unittest.main()
