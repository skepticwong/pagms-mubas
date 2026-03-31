
from app import create_app
from models import db, Grant, BudgetCategory, BudgetVirement, ApprovalWorkflow, ComplianceMonitoring

app = create_app()
with app.app_context():
    print("Running db.create_all()...")
    db.create_all()
    print("Database initialization complete.")
    
    # Check for new columns
    grant = Grant.query.first()
    if grant:
        print(f"Grant indirect_cost_rate: {grant.indirect_cost_rate}")
    
    cat = BudgetCategory.query.first()
    if cat:
        print(f"BudgetCategory encumbered: {cat.encumbered}")
        
    print("Schema verification complete.")
