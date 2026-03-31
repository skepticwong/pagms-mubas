
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from flask import Flask
from models import db, Grant, User, Asset, GrantKPI, BudgetCategory
from services.report_service import ReportService
from services.closeout_service import generate_final_report

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Setup mock data
    pi = User(name="Dr. Test PI", email="pi@test.com", role="PI")
    db.session.add(pi)
    db.session.commit()
    
    grant = Grant(
        title="Test Grant For Dossier",
        funder="Test Foundation",
        grant_code="TGD-2026-001",
        start_date=datetime(2025, 1, 1).date(),
        end_date=datetime(2026, 1, 1).date(),
        total_budget=100000.0,
        pi_id=pi.id,
        status="closed",
        archive_hash="abc123hash",
        archived_at=datetime.utcnow()
    )
    db.session.add(grant)
    db.session.commit()
    
    # Add budget category
    cat = BudgetCategory(grant_id=grant.id, name="Field Work", allocated=50000.0, spent=45000.0)
    db.session.add(cat)
    
    # Add Asset
    asset = Asset(
        name="Test Laptop",
        asset_tag="MUBAS-IT-001",
        grant_id=grant.id,
        status="TRANSFERRED",
        disposition_date=datetime(2026, 1, 15).date(),
        source_type="PURCHASED"
    )
    db.session.add(asset)
    
    # Add KPI
    kpi = GrantKPI(
        name="Papers Published",
        grant_id=grant.id,
        grant_wide_target=5,
        unit="papers"
    )
    db.session.add(kpi)
    db.session.commit()
    
    # Test generation
    print("Testing generate_final_report...")
    report_data = generate_final_report(grant.id)
    print(f"Report Data keys: {report_data.keys()}")
    print(f"Asset log: {report_data['asset_disposition_log']}")
    print(f"KPI achievements: {report_data['kpi_achievements']}")
    
    print("\nTesting generate_closeout_dossier_pdf...")
    output_pdf = "test_dossier.pdf"
    ReportService.generate_closeout_dossier_pdf(grant.id, output_pdf)
    
    if os.path.exists(output_pdf):
        print(f"SUCCESS: {output_pdf} generated.")
        print(f"File size: {os.path.getsize(output_pdf)} bytes")
    else:
        print("FAILURE: PDF not generated.")
