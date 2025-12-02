
from app import create_app
from models import db, Task, EvidenceSubmission, User, Grant
from services.task_service import TaskService
from datetime import datetime, date

app = create_app()

def verify_logic():
    with app.app_context():
        print("\n--- Verifying Evidence Review Logic ---")
        
        # 1. Setup mock data if needed or use existing
        # For safety in this environment, we just check the logic on a trial object
        
        # Create a dummy task and evidence for testing (will rollback)
        try:
            pi = User.query.filter_by(role='PI').first()
            team = User.query.filter_by(role='Team').first()
            grant = Grant.query.first()
            
            if not all([pi, team, grant]):
                print("Missing required data (PI, Team, or Grant) to run verification.")
                return

            task = Task(grant_id=grant.id, assigned_to=team.id, title="Test Verification", task_type="Fieldwork", deadline=date.today(), status='submitted')
            db.session.add(task)
            db.session.flush()
            
            evidence = EvidenceSubmission(task_id=task.id, hours_worked=5, verification_status='pending', activity_notes="Initial notes")
            db.session.add(evidence)
            db.session.flush()
            
            print(f"Initial: Task Status={task.status}, Evidence Status={evidence.verification_status}")
            
            # Test Approval
            TaskService.verify_evidence(evidence.id, 'approved', pi.id)
            print(f"After Approval: Task Status={task.status}, Evidence Status={evidence.verification_status}")
            
            # Test Revision Request
            TaskService.verify_evidence(evidence.id, 'revision_requested', pi.id, notes="Please do more")
            print(f"After Revision: Task Status={task.status}, Evidence Status={evidence.verification_status}")
            print(f"Notes: {evidence.activity_notes}")
            
            print("\nLogic Verification: SUCCESS")
            
        except Exception as e:
            print(f"Verification Failed: {e}")
        finally:
            db.session.rollback()

if __name__ == "__main__":
    verify_logic()
