import unittest
import json
from datetime import datetime
from app import create_app
from models import db, User, Grant, BudgetCategory, Rule, RuleProfile, RuleProfileSnapshot

class TestRulesIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Setup Data
        self.rsu_admin = User(name="RSU Admin", email="rsu@test.com", role="RSU")
        self.pi_user = User(name="Test PI", email="pi@test.com", role="PI")
        db.session.add_all([self.rsu_admin, self.pi_user])
        db.session.commit()

        # Create Funder Rules
        rule1 = Rule(
            name="Block High Equipment",
            rule_type="THRESHOLD",
            logic_config=json.dumps({"field": "amount", "operator": "greater_than", "value": 5000, "applies_to": "Equipment"}),
            outcome="BLOCK",
            created_by_id=self.rsu_admin.id,
            is_active=True
        )
        rule3 = Rule(
            name="Block Unapproved Co-PIs",
            rule_type="PERSONNEL",
            logic_config=json.dumps({"field": "role", "operator": "equals", "value": "Co-Investigator"}),
            outcome="BLOCK",
            guidance_text="Co-Investigators must be added during grant creation, not after.",
            created_by_id=self.rsu_admin.id,
            is_active=True
        )
        rule4 = Rule(
            name="Block Large Reallocations",
            rule_type="BUDGET",
            logic_config=json.dumps({"field": "amount", "operator": "greater_than", "value": 10000}),
            outcome="BLOCK",
            guidance_text="Cannot reallocate more than $10,000 without Funder approval.",
            created_by_id=self.rsu_admin.id,
            is_active=True
        )
        rule5 = Rule(
            name="Require Field for EU",
            rule_type="REQUIREMENT",
            logic_config=json.dumps({"field": "special_requirements", "operator": "is_empty", "value": True}),
            outcome="BLOCK",
            guidance_text="EU grants must have special requirements documented.",
            created_by_id=self.rsu_admin.id,
            is_active=True
        )
        db.session.add_all([rule1, rule3, rule4, rule5])
        db.session.commit()

        # Create Profile
        self.profile = RuleProfile(name="Strict Funder Profile", funder_id=1, created_by_id=self.rsu_admin.id, is_active=True)
        self.profile.rules = [rule1, rule3, rule4, rule5]
        db.session.add(self.profile)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        try:
            db.drop_all()
        except:
            pass # ignore cycle error since SQLite in memory destroys itself anyway
        self.app_context.pop()

    def test_grant_creation_blocked(self):
        """Test that a grant missing a required field is blocked."""
        from services.grant_service import GrantService
        
        data = {
            'title': 'Test Grant',
            'funder': 'Strict Funder',
            'grant_code': 'G-100',
            'funder_reference_number': 'FRN-1',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'total_budget': '50000',
            'rule_profile_id': self.profile.id,
            'special_requirements': '' # Empty to trigger rule
        }
        
        class DummyFiles:
            def get(self, key):
                return None

        with self.assertRaises(ValueError) as context:
            GrantService.create_grant(data, DummyFiles(), self.pi_user.id)
        
        self.assertIn("blocked by funder rules", str(context.exception))
        self.assertIn("EU grants must have special requirements documented", str(context.exception))

    def test_personnel_change_blocked(self):
        """Test that adding a Co-PI is blocked by rules."""
        from services.grant_team_service import GrantTeamService
        
        grant = Grant(
            title="Test Grant", funder="Other", grant_code="G-101", 
            start_date=datetime.now().date(), end_date=datetime.now().date(),
            total_budget=50000, pi_id=self.pi_user.id, rule_profile_id=self.profile.id
        )
        db.session.add(grant)
        
        team_member = User(name="Team Member", email="team@test.com", role="Team")
        db.session.add(team_member)
        db.session.commit()

        with self.assertRaises(ValueError) as context:
            GrantTeamService.add_team_member_to_grant(grant.id, team_member.id, "Co-Investigator", self.pi_user.id)
        
        self.assertIn("Personnel change blocked", str(context.exception))
        self.assertIn("Co-Investigators must be added during grant creation, not after.", str(context.exception))

    def test_budget_reallocation_blocked(self):
        """Test that large budget reallocations are blocked."""
        from services.budget_reallocation_service import BudgetReallocationService
        
        grant = Grant(
            title="Test Grant", funder="Other", grant_code="G-102", 
            start_date=datetime.now().date(), end_date=datetime.now().date(),
            total_budget=50000, pi_id=self.pi_user.id, rule_profile_id=self.profile.id
        )
        db.session.add(grant)
        db.session.commit()

        cat1 = BudgetCategory(grant_id=grant.id, name="Travel", allocated=20000)
        cat2 = BudgetCategory(grant_id=grant.id, name="Supplies", allocated=5000)
        db.session.add_all([cat1, cat2])
        db.session.commit()

        with self.assertRaises(ValueError) as context:
            # Try to move 15000, which is > 10000 rule
            BudgetReallocationService.reallocate(grant.id, cat1.id, cat2.id, 15000, self.pi_user.id)
        
        self.assertIn("Reallocation Blocked", str(context.exception))
        self.assertIn("Cannot reallocate more than $10,000 without Funder approval.", str(context.exception))

    def test_expense_submission_blocked(self):
        """Test that expenses violating rules are blocked at the route level."""
        grant = Grant(
            title="Test Grant", funder="Other", grant_code="G-103", 
            start_date=datetime.now().date(), end_date=datetime.now().date(),
            total_budget=50000, pi_id=self.pi_user.id, rule_profile_id=self.profile.id
        )
        db.session.add(grant)
        db.session.commit()

        cat = BudgetCategory(grant_id=grant.id, name="Equipment", allocated=10000)
        db.session.add(cat)
        db.session.commit()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = self.pi_user.id

        response = client.post('/api/expenses', data={
            'grant_id': grant.id,
            'category': 'Equipment',
            'amount': '6000', # > 5000 rule
            'expense_date': '2026-06-01',
            'rate_type': 'buying',
            'description': 'Laptops',
            'payment_method': 'card'
        })

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertTrue(data.get('rule_blocked'))
        self.assertIn("Compliance Block", data.get('error'))

if __name__ == '__main__':
    unittest.main()
