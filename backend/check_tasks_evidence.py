
from app import create_app
from models import db, Task, DeliverableSubmission, User

app = create_app()

def check_tasks_and_evidence():
    with app.app_context():
        print("\n--- TASKS ---")
        tasks = Task.query.all()
        for t in tasks:
            print(f"ID: {t.id} | Title: {t.title} | Status: {t.status} | Grant: {t.grant_id} | Assigned To: {t.assigned_to}")
        
        print("\n--- DELIVERABLE SUBMISSIONS ---")
        deliverable = DeliverableSubmission.query.all()
        for e in deliverable:
            print(f"ID: {e.id} | Task ID: {e.task_id} | Status: {e.verification_status} | Notes: {e.activity_notes}")

if __name__ == "__main__":
    check_tasks_and_evidence()
