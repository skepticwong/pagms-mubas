
from app import create_app
from models import db, Rule, RuleProfile

app = create_app()

with app.app_context():
    rules_count = Rule.query.count()
    profiles_count = RuleProfile.query.count()
    print(f"DEBUG: Rules in DB: {rules_count}")
    print(f"DEBUG: Profiles in DB: {profiles_count}")
    
    profiles = RuleProfile.query.all()
    for p in profiles:
        print(f"DEBUG: Profile: {p.name} -> Funder: {p.funder_id} (Rules: {len(p.rules)})")
