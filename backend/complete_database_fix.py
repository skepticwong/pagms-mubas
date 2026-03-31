#!/usr/bin/env python3
"""
Complete database verification and fix script
"""

import os
import sqlite3
import shutil
from datetime import datetime, date

def verify_and_fix_database():
    """Verify all required tables and data exist"""
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(backend_dir, 'instance', 'pagms.db')
    
    print("🔧 Complete Database Verification and Fix")
    print("=" * 50)
    
    # Remove existing database and start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Removed existing database")
    
    # Ensure instance directory exists
    instance_dir = os.path.dirname(db_path)
    os.makedirs(instance_dir, exist_ok=True)
    
    # Create fresh database using SQLAlchemy
    import sys
    sys.path.insert(0, backend_dir)
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from models import (db, User, Grant, FunderProfile, Task, 
                          DeliverableSubmission, ExpenseClaim, GrantTeam)
        
        # Create all tables
        db.create_all()
        print("✅ Created all database tables")
        
        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Tables created: {len(tables)}")
        
        required_tables = ['users', 'grants', 'funder_profiles', 'tasks', 'deliverable_submissions', 'expense_claims', 'grant_team']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            print(f"❌ Missing tables: {missing}")
            return False
        else:
            print("✅ All required tables present")
        
        # Check grants table structure specifically
        cursor.execute('PRAGMA table_info(grants)')
        columns = cursor.fetchall()
        has_funder_id = any(col[1] == 'funder_id' for col in columns)
        
        if not has_funder_id:
            print("❌ funder_id column still missing!")
            return False
        else:
            print("✅ funder_id column exists")
        
        conn.close()
        
        # Add comprehensive sample data
        print("\n🌱 Adding sample data...")
        
        # Clear existing data
        db.session.query(GrantTeam).delete()
        db.session.query(DeliverableSubmission).delete()
        db.session.query(ExpenseClaim).delete()
        db.session.query(Task).delete()
        db.session.query(Grant).delete()
        db.session.query(FunderProfile).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # Create funder profiles
        funders = [
            FunderProfile(
                name='National Science Foundation',
                contact_email='grants@nsf.gov',
                reporting_requirements='Quarterly reports, annual financial statements',
                compliance_framework='NSF Compliance'
            ),
            FunderProfile(
                name='Private Foundation',
                contact_email='contact@foundation.org',
                reporting_requirements='Annual reports, financial statements',
                compliance_framework='Standard Compliance'
            ),
            FunderProfile(
                name='National Institutes of Health',
                contact_email='grants@nih.gov',
                reporting_requirements='Monthly progress reports, annual financial reports',
                compliance_framework='NIH Compliance'
            )
        ]
        
        for funder in funders:
            db.session.add(funder)
        db.session.commit()
        print("✅ Created funder profiles")
        
        # Create users
        users = [
            User(
                name='Dr. John Smith',
                email='john.smith@university.edu',
                role='PI',
                pay_rate=85.0
            ),
            User(
                name='Jane Doe',
                email='jane.doe@university.edu',
                role='Team',
                pay_rate=65.0
            ),
            User(
                name='Admin User',
                email='admin@pagms.com',
                role='PI',
                pay_rate=100.0
            )
        ]
        
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        db.session.commit()
        print("✅ Created users")
        
        # Create grants
        grants = [
            Grant(
                title='Climate Change Research Project',
                grant_code='NSF-2024-001',
                funder_id=funders[0].id,
                pi_id=users[0].id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                total_budget=150000.0,
                currency='USD',
                status='active'
            ),
            Grant(
                title='Medical Research Study',
                grant_code='NIH-2024-002',
                funder_id=funders[2].id,
                pi_id=users[2].id,
                start_date=date(2024, 3, 1),
                end_date=date(2025, 2, 28),
                total_budget=200000.0,
                currency='USD',
                status='active'
            )
        ]
        
        for grant in grants:
            db.session.add(grant)
        db.session.commit()
        print("✅ Created grants")
        
        # Create grant teams
        for i, grant in enumerate(grants):
            team_entries = [
                GrantTeam(grant_id=grant.id, user_id=users[i].id, role='PI', status='active'),
                GrantTeam(grant_id=grant.id, user_id=users[(i+1)%3].id, role='Researcher', status='active')
            ]
            for entry in team_entries:
                db.session.add(entry)
        db.session.commit()
        print("✅ Created grant teams")
        
        # Create tasks
        tasks = [
            Task(
                grant_id=grants[0].id,
                assigned_to=users[1].id,
                title='Collect field samples',
                task_type='Field Work',
                deadline=datetime(2024, 6, 15),
                estimated_hours=40.0,
                status='IN_PROGRESS'
            ),
            Task(
                grant_id=grants[0].id,
                assigned_to=users[0].id,
                title='Analyze laboratory results',
                task_type='Lab Test',
                deadline=datetime(2024, 8, 1),
                estimated_hours=30.0,
                status='PENDING'
            ),
            Task(
                grant_id=grants[1].id,
                assigned_to=users[2].id,
                title='Patient recruitment',
                task_type='Clinical Work',
                deadline=datetime(2024, 7, 1),
                estimated_hours=50.0,
                status='ASSIGNED'
            )
        ]
        
        for task in tasks:
            db.session.add(task)
        db.session.commit()
        print("✅ Created tasks")
        
        # Create deliverable submissions
        submissions = [
            DeliverableSubmission(
                task_id=tasks[0].id,
                user_id=users[1].id,
                hours_worked=8.0,
                activity_notes='Collected water samples from 5 locations',
                verification_status='pending'
            ),
            DeliverableSubmission(
                task_id=tasks[1].id,
                user_id=users[0].id,
                hours_worked=4.0,
                activity_notes='Preliminary data analysis',
                verification_status='pending'
            )
        ]
        
        for submission in submissions:
            db.session.add(submission)
        db.session.commit()
        print("✅ Created deliverable submissions")
        
        # Create expense claims
        expenses = [
            ExpenseClaim(
                grant_id=grants[0].id,
                submitted_by=users[0].id,
                category='Travel',
                amount=250.0,
                description='Travel to field site for sample collection',
                expense_date=date(2024, 5, 15),
                status='pending'
            ),
            ExpenseClaim(
                grant_id=grants[1].id,
                submitted_by=users[2].id,
                category='Supplies',
                amount=150.0,
                description='Laboratory supplies',
                expense_date=date(2024, 5, 20),
                status='pending'
            )
        ]
        
        for expense in expenses:
            db.session.add(expense)
        db.session.commit()
        print("✅ Created expense claims")
        
        # Final verification
        print("\n📊 Final Database Summary:")
        print(f"  Users: {User.query.count()}")
        print(f"  Grants: {Grant.query.count()}")
        print(f"  Funder Profiles: {FunderProfile.query.count()}")
        print(f"  Tasks: {Task.query.count()}")
        print(f"  Deliverable Submissions: {DeliverableSubmission.query.count()}")
        print(f"  Expense Claims: {ExpenseClaim.query.count()}")
        print(f"  Grant Teams: {GrantTeam.query.count()}")
        
        # Test a sample query
        try:
            grant = Grant.query.first()
            print(f"\n✅ Test query successful: {grant.grant_code}")
            print(f"  Funder ID: {grant.funder_id}")
            print(f"  PI ID: {grant.pi_id}")
        except Exception as e:
            print(f"\n❌ Test query failed: {e}")
            return False
        
        print("\n🎉 Database setup completed successfully!")
        return True

if __name__ == '__main__':
    success = verify_and_fix_database()
    if not success:
        exit(1)
