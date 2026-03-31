import hashlib
import json
from datetime import datetime
from sqlalchemy import func
from models import db, Grant, ExpenseClaim, BudgetVirement, Asset, EffortCertification, Task, Milestone, GrantKPI, BudgetCategory

def get_closeout_status(grant_id):
    """
    Evaluates the 'Hard Gate' closeout requirements for a grant.
    Returns a dictionary of the 4 key compliance areas and an overall ready status.
    """
    grant = Grant.query.get(grant_id)
    if not grant:
        return None

    # 1. Financial Reconciliation
    pending_expenses = ExpenseClaim.query.filter_by(grant_id=grant_id, status='pending').all()
    pending_virements = BudgetVirement.query.filter_by(grant_id=grant_id, status='pending').all()
    financial_ready = len(pending_expenses) == 0 and len(pending_virements) == 0
    financial_blockers = []
    if pending_expenses:
        financial_blockers.append(f"{len(pending_expenses)} pending expense claims.")
    if pending_virements:
        financial_blockers.append(f"{len(pending_virements)} pending budget virements.")

    # 2. Asset Accountability
    # Assets must not be in an active/custody state. Safe states: RETURNED, TRANSFERRED, DISPOSED
    safe_asset_states = ['RETURNED', 'TRANSFERRED', 'DISPOSED']
    active_assets = Asset.query.filter_by(grant_id=grant_id).filter(~Asset.status.in_(safe_asset_states)).all()
    assets_ready = len(active_assets) == 0
    asset_blockers = [f"{a.name} ({a.asset_tag}) is marked as {a.status}." for a in active_assets]

    # 3. Personnel Compliance
    # Check that there are no pending certifications
    pending_certs = EffortCertification.query.filter_by(grant_id=grant_id, status='PENDING').all()
    personnel_ready = len(pending_certs) == 0
    personnel_blockers = [f"Pending effort certification for {cert.user.name if cert.user else 'User'} ({cert.certification_period})." for cert in pending_certs]

    # 4. Deliverable Completion
    # All milestones must be completed, all tasks completed
    incomplete_milestones = Milestone.query.filter_by(grant_id=grant_id).filter(func.upper(Milestone.status) != 'COMPLETED').all()
    incomplete_tasks = Task.query.filter_by(grant_id=grant_id).filter(func.upper(Task.status).notin_(['COMPLETED', 'CANCELLED'])).all()
    
    deliverables_ready = len(incomplete_milestones) == 0 and len(incomplete_tasks) == 0
    deliverable_blockers = []
    for m in incomplete_milestones:
        deliverable_blockers.append(f"Milestone '{m.title}' is not complete.")
    if incomplete_tasks:
        deliverable_blockers.append(f"{len(incomplete_tasks)} tasks are not complete.")

    overall_ready = financial_ready and assets_ready and personnel_ready and deliverables_ready

    return {
        "grant_id": grant.id,
        "is_ready": overall_ready,
        "is_archived": bool(grant.archive_hash),
        "archived_at": grant.archived_at.isoformat() if grant.archived_at else None,
        "archive_hash": grant.archive_hash,
        "checklist": {
            "financial": {
                "ready": financial_ready,
                "blockers": financial_blockers
            },
            "assets": {
                "ready": assets_ready,
                "blockers": asset_blockers
            },
            "personnel": {
                "ready": personnel_ready,
                "blockers": personnel_blockers
            },
            "deliverables": {
                "ready": deliverables_ready,
                "blockers": deliverable_blockers
            }
        }
    }

def generate_final_report(grant_id):
    """
    Generates the comprehensive JSON dossier for the final closing report.
    This includes financial burn, asset dispositions, and KPI completion.
    """
    grant = Grant.query.get(grant_id)
    if not grant:
        return None

    # Financials
    categories = BudgetCategory.query.filter_by(grant_id=grant_id).all()
    finances = []
    total_approved = 0
    total_spent = 0
    for cat in categories:
        finances.append({
            "category": cat.name,
            "approved_amount": cat.allocated,
            "actual_spend": cat.spent or 0,
            "variance": cat.allocated - (cat.spent or 0),
            "utilized_percent": round(((cat.spent or 0) / cat.allocated * 100) if cat.allocated else 0, 2)
        })
        total_approved += cat.allocated
        total_spent += cat.spent or 0

    # Assets
    assets = Asset.query.filter_by(grant_id=grant_id).all()
    asset_log = []
    for a in assets:
        asset_log.append({
            "asset_tag": a.asset_tag,
            "name": a.name,
            "final_status": a.status,
            "disposition_date": a.disposition_date.isoformat() if a.disposition_date else None
        })

    # KPIs
    kpis = GrantKPI.query.filter_by(grant_id=grant_id).all()
    kpi_log = []
    for k in kpis:
        kpi_log.append({
            "name": k.name,
            "target": k.grant_wide_target,
            "achieved": k.total_actual,
            "status": k.status
        })

    report = {
        "grant_code": grant.grant_code,
        "title": grant.title,
        "funder": grant.funder,
        "end_date": grant.end_date.isoformat() if grant.end_date else None,
        "generated_on": datetime.utcnow().isoformat(),
        "financial_summary": {
            "total_approved": total_approved,
            "total_spent": total_spent,
            "overall_utilization": round((total_spent / total_approved * 100) if total_approved else 0, 2),
            "categories": finances
        },
        "asset_disposition_log": asset_log,
        "kpi_achievements": kpi_log
    }
    return report

def lock_grant_archive(grant_id, user_id):
    """
    Phase 2 lock: Generates final report, creates SHA-256 hash, and archives.
    """
    grant = Grant.query.get(grant_id)
    if not grant:
        return {"success": False, "error": "Grant not found"}
        
    status_check = get_closeout_status(grant_id)
    if not status_check or not status_check['is_ready']:
        return {"success": False, "error": "Closeout gates not completed. Cannot archive."}
        
    report_data = generate_final_report(grant_id)
    # create deterministic json string for hashing
    json_str = json.dumps(report_data, sort_keys=True)
    secret_salt = "MUBAS_SECURE_ARCHIVE_2026"
    
    # Generate SHA-256 Hash
    archive_hash = hashlib.sha256((json_str + secret_salt + str(grant_id)).encode('utf-8')).hexdigest()
    
    grant.archive_hash = archive_hash
    grant.archived_at = datetime.utcnow()
    grant.status = 'closed'
    
    db.session.commit()
    
    return {
        "success": True, 
        "message": "Grant successfully closed and mathematically archived.",
        "archive_hash": archive_hash,
        "archived_at": grant.archived_at.isoformat()
    }
