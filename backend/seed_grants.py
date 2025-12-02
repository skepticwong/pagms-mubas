
from app import create_app
from models import db, User, Grant, BudgetCategory, Milestone
from datetime import datetime, date, timedelta

app = create_app()

with app.app_context():
    print("🌱 Seeding database with ADDITONAL grants...")

    # 1. Ensure PI exists
    pi_email = 'pi@mubas.ac.mw'
    pi = User.query.filter_by(email=pi_email).first()
    if not pi:
        print(f"User {pi_email} not found. Please run app.py first to create default users.")
        exit(1)

    # 3. Grant 3: Digital Health
    grant3 = Grant(
        title='Digital Health Scale-Up Initiative',
        funder='Bill & Melinda Gates Foundation',
        grant_code='BMGF-DH-2025-09',
        funder_reference_number='OPP-112233',
        start_date=date(2025, 2, 1),
        end_date=date(2027, 1, 31),
        total_budget=420000.0,
        currency='USD',
        exchange_rate=1750.0,
        financial_reporting_frequency='monthly',
        pi_id=pi.id,
        status='active'
    )
    db.session.add(grant3)
    db.session.flush()

    db.session.add(BudgetCategory(grant_id=grant3.id, name='Software Dev', allocated=200000.0, spent=10000.0))
    db.session.add(BudgetCategory(grant_id=grant3.id, name='Hardware', allocated=120000.0, spent=50000.0))
    db.session.add(BudgetCategory(grant_id=grant3.id, name='Training', allocated=100000.0, spent=0.0))
    
    db.session.add(Milestone(
        grant_id=grant3.id, 
        title='Prototype Launch', 
        due_date=date(2025, 8, 1),
        status='not_started'
    ))

    # 4. Grant 4: STEM Education
    grant4 = Grant(
        title='Inclusive STEM Education for Rural Girls',
        funder='UNICEF',
        grant_code='UN-STEM-MW-2024',
        funder_reference_number='MW-EDU-005',
        start_date=date(2024, 1, 1),
        end_date=date(2026, 12, 31),
        total_budget=280000.0,
        currency='USD',
        exchange_rate=1750.0,
        financial_reporting_frequency='quarterly',
        pi_id=pi.id,
        status='active'
    )
    db.session.add(grant4)
    db.session.flush()

    db.session.add(BudgetCategory(grant_id=grant4.id, name='School Materials', allocated=100000.0, spent=95000.0))
    db.session.add(BudgetCategory(grant_id=grant4.id, name='Workshops', allocated=100000.0, spent=40000.0))
    db.session.add(BudgetCategory(grant_id=grant4.id, name='M&E', allocated=80000.0, spent=20000.0))

    db.session.add(Milestone(
        grant_id=grant4.id, 
        title='Annual Impact Report', 
        due_date=date(2025, 1, 31),
        status='completed'
    ))

    db.session.commit()
    print("✅ Successfully added 2 NEW grants!")
