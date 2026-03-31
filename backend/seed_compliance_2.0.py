# backend/seed_compliance_2.0.py
import sys
import os

# Add the current directory to path so we can import app and models
sys.path.append(os.getcwd())

from app import app
from models import db, Rule, FunderProfile, User
import json

def seed():
    with app.app_context():
        print("Starting Compliance 2.0 Seeding...")
        
        # 1. Get or Create RSU Admin for linking
        admin = User.query.filter_by(role='RSU').first()
        if not admin:
            # Create a default system admin if none exists
            from werkzeug.security import generate_password_hash
            admin = User(
                name="RSU Compliance Admin",
                email="rsu@mubas.mw",
                password_hash=generate_password_hash("compliance20"),
                role="RSU"
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default RSU Admin: rsu@mubas.mw")

        # 2. Create Global Rules
        # We use a dictionary to track rules by name for easy linking
        rules_data = [
            {
                "name": "Single Expense Limit (MWK 5M)",
                "rule_type": "EXPENSE_LIMIT",
                "logic_config": {"max_amount": 5000000},
                "outcome": "PRIOR_APPROVAL",
                "guidance_text": "Any single expense exceeding MWK 5,000,000 requires prior RSU approval."
            },
            {
                "name": "Alcohol & Tobacco Prohibition",
                "rule_type": "DESCRIPTION_MATCH",
                "logic_config": {"keywords": ["alcohol", "tobacco", "cigarette", "liquor", "beer", "wine", "spirit"]},
                "outcome": "BLOCK",
                "guidance_text": "Expenses for alcohol or tobacco are strictly prohibited by all funders."
            },
            {
                "name": "Uncategorized Spending Block",
                "rule_type": "CATEGORY_MATCH",
                "logic_config": {"forbidden_categories": ["Miscellaneous", "Other", "Unknown"]},
                "outcome": "BLOCK",
                "guidance_text": "All expenses must be mapped to a valid budget category. 'Miscellaneous' is not allowed."
            },
            {
                "name": "International Travel Audit",
                "rule_type": "CATEGORY_MATCH",
                "logic_config": {"special_categories": ["International Travel"]},
                "outcome": "WARN",
                "guidance_text": "International travel expenses trigger an automatic compliance flag for audit review."
            }
        ]

        active_rules = []
        for r_info in rules_data:
            rule = Rule.query.filter_by(name=r_info['name']).first()
            if not rule:
                rule = Rule(
                    name=r_info['name'],
                    rule_type=r_info['rule_type'],
                    logic_config=r_info['logic_config'], # models.py uses db.JSON, so pass dict
                    outcome=r_info['outcome'],
                    guidance_text=r_info['guidance_text'],
                    created_by_id=admin.id
                )
                db.session.add(rule)
            else:
                # Update existing rule
                rule.logic_config = r_info['logic_config']
                rule.outcome = r_info['outcome']
                rule.guidance_text = r_info['guidance_text']
            active_rules.append(rule)
        
        db.session.commit()
        print(f"Seeded {len(active_rules)} standard rules.")

        # 3. Create Funder Profiles
        funder_defs = [
            {"name": "World Bank (WB)", "funder_id": "wb"},
            {"name": "National Research Fund (NRF)", "funder_id": "nrf"},
            {"name": "USAID", "funder_id": "usaid"},
            {"name": "EU Horizon", "funder_id": "eu"},
            {"name": "Bill & Melinda Gates Foundation", "funder_id": "gates"},
        ]

        for f_info in funder_defs:
            profile = FunderProfile.query.filter_by(funder_id=f_info['funder_id']).first()
            if not profile:
                profile = FunderProfile(
                    name=f_info['name'],
                    funder_id=f_info['funder_id'],
                    created_by_id=admin.id,
                    is_active=True
                )
                db.session.add(profile)
            
            # Ensure all standard rules are linked to this profile
            # We filter for rules that are not already in profile.rules
            existing_rule_ids = [r.id for r in profile.rules]
            for r in active_rules:
                if r.id not in existing_rule_ids:
                    profile.rules.append(r)
            
        db.session.commit()
        print(f"Seeded/Updated {len(funder_defs)} funder profiles with linked rules.")
        
        print("Compliance 2.0 Seeding Successfully Completed!")

if __name__ == "__main__":
    seed()
