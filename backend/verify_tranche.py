import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from models import db, User, Grant, Milestone
from services.grant_service import GrantService
import json
import uuid

with app.app_context():
    email = f"test_{uuid.uuid4()}@example.com"
    user = User(name="Test PI", email=email, role="PI")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    
    grant_code = f"TEST-TR-{str(uuid.uuid4())[:8]}"
    form_data = {
        'title': 'Tranche Test Grant',
        'funder': 'Test Funder',
        'grant_code': grant_code,
        'start_date': '2024-01-01',
        'end_date': '2025-01-01',
        'total_budget': '1000',
        'budget_categories': json.dumps([{'name': 'Personnel', 'allocated': '1000'}]),
        'milestones': json.dumps([{
            'title': 'Milestone 1',
            'due_date': '2024-06-01',
            'triggers_tranche': 2
        }])
    }
    
    try:
        grant = GrantService.create_grant(form_data, {}, user.id)
        print(f"Grant created ID: {grant.id}")
        
        milestone = Milestone.query.filter_by(grant_id=grant.id).first()
        print(f"Milestone triggers_tranche: {milestone.triggers_tranche}")
        assert milestone.triggers_tranche == 2, "Triggers tranche not saved!"
        print("Success: triggers_tranche saved to DB!")

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            
        res = client.get(f'/api/grants/{grant.id}/tranche-status?tranche_number=2')
        print(f"Route Status: {res.status_code}")
        print(f"Route Response: {res.get_json()}")
        assert res.status_code == 200, "Route failed!"
        print("Success: Route tested!")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
