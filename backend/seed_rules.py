
from app import create_app
from models import db, Grant, Rule, RuleProfile, User
import json
import os

app = create_app()

with app.app_context():
    # 1. Get existing funders from Grants
    funders = db.session.query(Grant.funder).distinct().all()
    funders = [f[0] for f in funders if f[0]]
    
    if not funders:
        print("No funders found in Grants table. Using defaults.")
        funders = ["NIH", "EU Horizon", "Ford Foundation", "World Bank"]
    
    print(f"Found funders: {funders}")

    # 2. Get an RSU user to be the creator
    rsu_user = User.query.filter_by(role='RSU').first()
    if not rsu_user:
        print("No RSU user found. Cannot seed.")
        exit(1)

    # 3. Define some standard rules
    standard_rules = [
        {
            "name": "Equipment Threshold $5,000",
            "rule_type": "THRESHOLD",
            "logic_config": {"field": "amount", "operator": "greater_than", "value": 5000, "applies_to": "equipment"},
            "outcome": "BLOCK",
            "priority_level": 1,
            "guidance_text": "Equipment purchases over $5,000 require prior RSU & Funder approval. Please split the request or seek an override."
        },
        {
            "name": "International Travel Approval",
            "rule_type": "CATEGORY_ALLOWABILITY",
            "logic_config": {"field": "amount", "operator": "greater_than", "value": 1000, "applies_to": "travel"},
            "outcome": "PRIOR_APPROVAL",
            "priority_level": 2,
            "guidance_text": "International travel expenses over $1,000 require prior approval from the RSU."
        },
        {
            "name": "Consultancy Rate Cap",
            "rule_type": "THRESHOLD",
            "logic_config": {"field": "amount", "operator": "greater_than", "value": 500, "applies_to": "consultancy"},
            "outcome": "WARN",
            "priority_level": 3,
            "guidance_text": "Standard consultancy rates should not exceed $500/day. High-rate justifications required."
        }
    ]

    created_rules = []
    for r_data in standard_rules:
        # Avoid duplicates
        existing_rule = Rule.query.filter_by(name=r_data['name']).first()
        if not existing_rule:
            new_rule = Rule(
                name=r_data['name'],
                rule_type=r_data['rule_type'],
                logic_config=json.dumps(r_data['logic_config']),
                outcome=r_data['outcome'],
                priority_level=r_data['priority_level'],
                guidance_text=r_data['guidance_text'],
                created_by_id=rsu_user.id,
                is_active=True
            )
            db.session.add(new_rule)
            created_rules.append(new_rule)
            print(f"Created rule: {new_rule.name}")
        else:
            created_rules.append(existing_rule)

    db.session.commit()

    # 4. Create Profiles for each funder
    for funder_name in funders:
        profile_name = f"{funder_name} Standard Compliance Profile"
        existing_profile = RuleProfile.query.filter_by(name=profile_name).first()
        
        if not existing_profile:
            new_profile = RuleProfile(
                name=profile_name,
                funder_id=funder_name,
                created_by_id=rsu_user.id,
                is_active=True
            )
            # Link all created rules to this profile for demo
            new_profile.rules = created_rules
            db.session.add(new_profile)
            print(f"Created profile for: {funder_name}")
        else:
            print(f"Profile for {funder_name} already exists.")

    db.session.commit()
    print("Seeding completed successfully.")
    os._exit(0)
