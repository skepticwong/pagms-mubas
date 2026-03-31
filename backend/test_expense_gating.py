import sys
import os
import json
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from models import db, User, Grant, Milestone, BudgetCategory, ExpenseClaim
from services.grant_service import GrantService

def test_gating():
    with app.app_context():
        # 1. Setup: Create PI and Grant
        email = f"pi_gate_{uuid.uuid4()}@example.com"
        pi = User(name="Gate PI", email=email, role="PI")
        pi.set_password("password")
        db.session.add(pi)
        
        finance_email = f"fin_gate_{uuid.uuid4()}@example.com"
        finance = User(name="Gate Finance", email=finance_email, role="Finance")
        finance.set_password("password")
        db.session.add(finance)
        db.session.commit()
        
        grant_code = f"GATE-{str(uuid.uuid4())[:6]}"
        grant = Grant(
            title="Gating Test Grant",
            funder="Test Funder",
            grant_code=grant_code,
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2025, 1, 1).date(),
            total_budget=3000.0,
            pi_id=pi.id,
            status='active'
        )
        db.session.add(grant)
        db.session.flush()
        
        from models import Milestone, BudgetCategory, Document, EffortCertification
        
        # Add budget category
        cat = BudgetCategory(grant_id=grant.id, name="Travel", allocated=3000.0)
        db.session.add(cat)
        
        # Add milestone for tranche 1
        m1 = Milestone(grant_id=grant.id, title="M1", due_date=datetime(2024, 2, 1).date(), triggers_tranche=1, status='COMPLETED')
        db.session.add(m1)

        # Add dummy Financial Report Document for Tranche 1
        report = Document(
            grant_id=grant.id,
            doc_type='Financial Report',
            file_name=f'Tranche 1 Financial Report - {grant_code}.pdf',
            file_path='/tmp/report.pdf',
            uploader_id=finance.id
        )
        db.session.add(report)

        # Add effort certification to bypass the 10th-day lock
        cert = EffortCertification(
            user_id=pi.id,
            grant_id=grant.id,
            period_month=2, # February
            period_year=2026,
            certification_period='2026-02',
            status='VERIFIED',
            is_pi_certification=True
        )
        db.session.add(cert)
        
        db.session.commit()
        
        print(f"Setup complete. Grant ID: {grant.id}. Disbursed: {grant.disbursed_funds}")
        
        client = app.test_client()
        
        # 2. Test: Submit expense with 0 disbursed funds (SHOULD FAIL)
        with client.session_transaction() as sess:
            sess['user_id'] = pi.id
            
        res = client.post('/api/expenses', data={
            'grant_id': grant.id,
            'category': 'Travel',
            'amount': '500',
            'expense_date': '2024-03-01',
            'description': 'Test travel'
        })
        
        print(f"Submit expense (0 disbursed) response: {res.status_code}")
        assert res.status_code == 403, "Expense succeeded with 0 disbursed funds!"
        print("Success: Expense blocked correctly.")
        
        # 3. Test: Release Tranche 1
        with client.session_transaction() as sess:
            sess['user_id'] = finance.id
            
        res = client.post('/api/finance/release-tranche', json={
            'grant_id': grant.id,
            'tranche_number': 1
        })
        
        print(f"Release Tranche 1 response: {res.status_code}")
        print(f"Release Tranche 1 data: {res.get_json()}")
        assert res.status_code == 200
        
        db.session.refresh(grant)
        print(f"New disbursed amount: {grant.disbursed_funds}")
        assert grant.disbursed_funds == 1000.0
        
        # 4. Test: Submit expense with 1000 disbursed funds (SHOULD SUCCEED)
        with client.session_transaction() as sess:
            sess['user_id'] = pi.id
            
        res = client.post('/api/expenses', data={
            'grant_id': grant.id,
            'category': 'Travel',
            'amount': '500',
            'expense_date': '2024-03-01',
            'description': 'Test travel'
        })
        
        print(f"Submit expense (after tranche) response: {res.status_code}")
        assert res.status_code == 201, f"Expense failed even after tranche release! {res.get_json()}"
        print("Success: Expense allowed after tranche release.")

if __name__ == "__main__":
    from datetime import datetime
    try:
        test_gating()
        print("\nALL GATING TESTS PASSED!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
