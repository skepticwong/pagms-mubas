#!/usr/bin/env python3
"""
Complete database setup with all required tables and sample data
"""

import os
from datetime import datetime, date

def setup_complete_database():
    """Set up complete database with all tables and sample data"""
    
    print("🔧 Setting up complete database...")
    
    # Remove existing database
    db_path = os.path.join('instance', 'pagms.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Removed existing database")
    
    # Create app and database
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from models import (db, User, Grant, FunderProfile, Task, 
                          DeliverableSubmission, ExpenseClaim, GrantTeam)
        
        # Create all tables
        db.create_all()
        print("✅ Created all database tables")
        
        # Create funder profiles
        funder1 = FunderProfile(
            name='National Science Foundation',
            contact_email='grants@nsf.gov',
            reporting_requirements='Quarterly reports, annual financial statements',
            compliance_framework='NSF Compliance'
        )
        funder2 = FunderProfile(
            name='Private Foundation',
            contact_email='contact@foundation.org',
            reporting_requirements='Annual reports, financial statements',
            compliance_framework='Standard Compliance'
        )
        db.session.add(funder1)
        db.session.add(funder2)
        db.session.commit()
        
        # Create users
        pi_user = User(
            name='Dr. John Smith',
            email='john.smith@university.edu',
            role='PI',
            pay_rate=85.0
        )
        pi_user.set_password('pi123')
        
        team_user = User(
            name='Jane Doe',
            email='jane.doe@university.edu',
            role='Team',
            pay_rate=65.0
        )
        team_user.set_password('team123')
        
        admin_user = User(
            name='Admin User',
            email='admin@pagms.com',
            role='PI',
            pay_rate=100.0
        )
        admin_user.set_password('admin123')
        
        db.session.add(pi_user)
        db.session.add(team_user)
        db.session.add(admin_user)
        db.session.commit()
        
        # Create grant
        grant = Grant(
            title='Climate Change Research Project',
            grant_code='NSF-2024-001',
            funder_id=funder1.id,
            pi_id=pi_user.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            total_budget=150000.0,
            currency='USD',
            status='active'
        )
        db.session.add(grant)
        db.session.commit()
        
        # Create grant team
        team_entry = GrantTeam(
            grant_id=grant.id,
            user_id=pi_user.id,
            role='PI',
            status='active'
        )
        db.session.add(team_entry)
        
        team_entry2 = GrantTeam(
            grant_id=grant.id,
            user_id=team_user.id,
            role='Researcher',
            status='active'
        )
        db.session.add(team_entry2)
        db.session.commit()
        
        # Create tasks
        task1 = Task(
            grant_id=grant.id,
            assigned_to=team_user.id,
            title='Collect field samples',
            task_type='Field Work',
            deadline=datetime(2024, 6, 15),
            estimated_hours=40.0,
            status='IN_PROGRESS'
        )
        
        task2 = Task(
            grant_id=grant.id,
            assigned_to=pi_user.id,
            title='Analyze laboratory results',
            task_type='Lab Test',
            deadline=datetime(2024, 8, 1),
            estimated_hours=30.0,
            status='PENDING'
        )
        
        db.session.add(task1)
        db.session.add(task2)
        db.session.commit()
        
        # Create deliverable submission
        submission = DeliverableSubmission(
            task_id=task1.id,
            user_id=team_user.id,
            hours_worked=8.0,
            activity_notes='Collected water samples from 5 locations',
            verification_status='pending'
        )
        db.session.add(submission)
        
        # Create expense claim
        expense = ExpenseClaim(
            grant_id=grant.id,
            submitted_by=pi_user.id,
            category='Travel',
            amount=250.0,
            description='Travel to field site for sample collection',
            expense_date=date(2024, 5, 15),
            status='pending'
        )
        db.session.add(expense)
        db.session.commit()
        
        print("✅ Added sample data")
        
        # Verify data
        print("\n📊 Database Summary:")
        print(f"  Users: {User.query.count()}")
        print(f"  Grants: {Grant.query.count()}")
        print(f"  Funder Profiles: {FunderProfile.query.count()}")
        print(f"  Tasks: {Task.query.count()}")
        print(f"  Deliverable Submissions: {DeliverableSubmission.query.count()}")
        print(f"  Expense Claims: {ExpenseClaim.query.count()}")
        print(f"  Grant Teams: {GrantTeam.query.count()}")
        
        print("\n🎉 Database setup completed successfully!")
        return True

if __name__ == '__main__':
    success = setup_complete_database()
    if not success:
        exit(1)
