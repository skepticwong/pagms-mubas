from app import create_app
from models import db, User, Grant, BudgetCategory, Milestone
import datetime

def restore_data():
    app = create_app()
    with app.app_context():
        pi = User.query.filter_by(email='pi@mubas.ac.mw').first()
        if not pi:
            print("PI user not found. Creating...")
            from services.auth_service import AuthService
            pi = AuthService.create_user('Dr. PI', 'pi@mubas.ac.mw', 'PI', 'mubas123')
        
        # Check if they have any grants
        grant_count = Grant.query.filter_by(pi_id=pi.id).count()
        if grant_count == 0:
            print(f"PI (ID: {pi.id}) has 0 grants. Seeding one...")
            g = Grant(
                title="MUBAS Smart Irrigation Research",
                funder="NERC",
                grant_code="MUBAS-SIR-2025",
                start_date=datetime.date(2025, 1, 1),
                end_date=datetime.date(2027, 12, 31),
                total_budget=500000.0,
                pi_id=pi.id,
                status="active",
                currency="USD"
            )
            db.session.add(g)
            db.session.flush()
            
            # Add categories
            db.session.add(BudgetCategory(grant_id=g.id, name="Personnel", allocated=300000.0, spent=45000.0))
            db.session.add(BudgetCategory(grant_id=g.id, name="Equipment", allocated=150000.0, spent=12000.0))
            db.session.add(BudgetCategory(grant_id=g.id, name="Travel", allocated=50000.0, spent=5000.0))
            
            # Add milestones
            db.session.add(Milestone(
                grant_id=g.id,
                title="Infrastructure Setup",
                due_date=datetime.date(2025, 6, 30),
                status="COMPLETED",
                completion_date=datetime.date(2025, 6, 15)
            ))
            
            db.session.commit()
            print("✅ Successfully restored sample grant data for PI.")
        else:
            print(f"PI already has {grant_count} grants. No action needed.")

if __name__ == "__main__":
    restore_data()
