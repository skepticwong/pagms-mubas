import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.getcwd())

from app import create_app
from models import db, Rule, RuleProfile

def seed_virement_rules():
    app = create_app()
    with app.app_context():
        print("--- seeding Virement Rules ---")
        
        # 1. threshold Rule
        rule1 = Rule.query.filter_by(name="virement_threshold_rsu").first()
        if not rule1:
            rule1 = Rule(
                name="virement_threshold_rsu",
                description="RSU approval required for virements over $5,000",
                category="virement",
                logic_config=json.dumps({
                    "field": "amount",
                    "operator": "greater_than",
                    "value": 5000
                }),
                outcome="PRIOR_APPROVAL",
                guidance_text="Transfers over $5,000 require RSU and Finance approval.",
                priority_level=2
            )
            db.session.add(rule1)

        # 2. Percentage Rule
        rule2 = Rule.query.filter_by(name="virement_percentage_cap").first()
        if not rule2:
            rule2 = Rule(
                name="virement_percentage_cap",
                description="RSU approval required if reallocating more than 10% of total budget",
                category="virement",
                logic_config=json.dumps({
                    "field": "percent_of_total",
                    "operator": "greater_than",
                    "value": 0.10
                }),
                outcome="PRIOR_APPROVAL",
                guidance_text="Reallocating more than 10% of the total budget requires prior approval.",
                priority_level=2
            )
            db.session.add(rule2)

        # 3. Forbidden Category Rule
        rule3 = Rule.query.filter_by(name="virement_personnel_lock").first()
        if not rule3:
            rule3 = Rule(
                name="virement_personnel_lock",
                description="Blocking transfers from Personnel category",
                category="virement",
                logic_config=json.dumps({
                    "field": "source_category",
                    "operator": "equals",
                    "value": "personnel",
                    "applies_to": "virement"
                }),
                outcome="BLOCK",
                guidance_text="Funds cannot be moved out of the Personnel budget category.",
                priority_level=1
            )
            db.session.add(rule3)

        db.session.commit()
        print("Virement rules seeded successfully.")
        
        # Link to General/Global profile if it exists
        profile = RuleProfile.query.filter_by(name="General").first()
        if profile:
            if rule1 not in profile.rules: profile.rules.append(rule1)
            if rule2 not in profile.rules: profile.rules.append(rule2)
            if rule3 not in profile.rules: profile.rules.append(rule3)
            db.session.commit()
            print("Rules linked to General profile.")

if __name__ == "__main__":
    seed_virement_rules()
