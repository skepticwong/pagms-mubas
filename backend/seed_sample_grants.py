from app import create_app
from models import db, Grant, User, BudgetCategory, Milestone
from datetime import date, datetime

def seed_sample_grants():
    app = create_app()
    with app.app_context():
        print("Clearing existing grants, budget categories, and milestones...")
        db.session.query(Milestone).delete()
        db.session.query(BudgetCategory).delete()
        db.session.query(Grant).delete()
        db.session.commit()
        print("Existing data cleared.")

        # Assuming PI user has ID 1, based on previous inspection
        pi_user = User.query.get(1)
        if not pi_user or pi_user.role != 'PI':
            print("Error: PI user with ID 1 not found or not a PI. Please ensure the PI user exists.")
            return

        # Sample Grant 1
        grant1 = Grant(
            title="Research on Climate Change Impact",
            funder="Environmental Research Foundation",
            grant_code="ERF-CC-2023-001",
            funder_reference_number="FRN-2023-A-01",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31),
            total_budget=150000.00,
            currency="USD",
            exchange_rate=1.0,
            pi_id=pi_user.id,
            status="active",
            financial_reporting_frequency="quarterly",
            progress_reporting_frequency="biannual",
            special_requirements="Open access publication required.",
            ethical_approval_filename="ethics_approval_001.pdf"
        )
        db.session.add(grant1)
        db.session.commit() # Commit to get grant1.id

        # Budget Categories for Grant 1
        budget_cat1_1 = BudgetCategory(grant_id=grant1.id, name="Personnel", allocated=75000.00, spent=10000.00)
        budget_cat1_2 = BudgetCategory(grant_id=grant1.id, name="Equipment", allocated=30000.00, spent=5000.00)
        budget_cat1_3 = BudgetCategory(grant_id=grant1.id, name="Travel", allocated=20000.00, spent=2000.00)
        db.session.add_all([budget_cat1_1, budget_cat1_2, budget_cat1_3])

        # Milestones for Grant 1
        milestone1_1 = Milestone(
            grant_id=grant1.id,
            title="Project Inception Report",
            description="Submission of initial project plan and team setup.",
            due_date=date(2023, 3, 31),
            reporting_period="q1_year1",
            status="completed",
            completion_date=date(2023, 3, 25)
        )
        milestone1_2 = Milestone(
            grant_id=grant1.id,
            title="Mid-term Progress Review",
            description="Review of project progress and preliminary findings.",
            due_date=date(2024, 6, 30),
            reporting_period="biannual_1",
            status="in_progress"
        )
        db.session.add_all([milestone1_1, milestone1_2])


        # Sample Grant 2
        grant2 = Grant(
            title="Community Health Initiative",
            funder="Global Health Alliance",
            grant_code="GHA-CHI-2023-005",
            funder_reference_number="FRN-2023-B-05",
            start_date=date(2023, 6, 1),
            end_date=date(2025, 5, 31),
            total_budget=250000.00,
            currency="USD",
            exchange_rate=1.0,
            pi_id=pi_user.id,
            status="pending",
            financial_reporting_frequency="annual",
            progress_reporting_frequency="annual",
            special_requirements="Community engagement reports.",
            ethical_approval_filename="ethics_approval_002.pdf"
        )
        db.session.add(grant2)
        db.session.commit() # Commit to get grant2.id

        # Budget Categories for Grant 2
        budget_cat2_1 = BudgetCategory(grant_id=grant2.id, name="Personnel", allocated=120000.00, spent=0.00)
        budget_cat2_2 = BudgetCategory(grant_id=grant2.id, name="Supplies", allocated=50000.00, spent=0.00)
        budget_cat2_3 = BudgetCategory(grant_id=grant2.id, name="Community Outreach", allocated=80000.00, spent=0.00)
        db.session.add_all([budget_cat2_1, budget_cat2_2, budget_cat2_3])

        # Milestones for Grant 2
        milestone2_1 = Milestone(
            grant_id=grant2.id,
            title="Baseline Study Completion",
            description="Completion of initial community health assessment.",
            due_date=date(2023, 9, 30),
            reporting_period="q1_year1",
            status="not_started"
        )
        milestone2_2 = Milestone(
            grant_id=grant2.id,
            title="Intervention Launch",
            description="Official launch of health intervention programs.",
            due_date=date(2024, 3, 31),
            reporting_period="biannual_1",
            status="not_started"
        )
        db.session.add_all([milestone2_1, milestone2_2])

        db.session.commit()
        print(f"Added 2 sample grants with detailed data for PI user {pi_user.name} (ID: {pi_user.id}).")

if __name__ == "__main__":
    seed_sample_grants()