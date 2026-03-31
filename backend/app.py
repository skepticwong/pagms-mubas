# backend/app.py
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# ✅ IMPORT db from models — NOT creating a new one
from models import db
from routes.auth import auth_bp
from routes.grants import grants_bp
from routes.misc import misc_bp
from routes.tasks import tasks_bp
from routes.users import users_bp
from routes.reports import reports_bp
from routes.expenses import expenses_bp
from routes.finance import finance_bp
from routes.documents import documents_bp
from routes.rules import rules_bp
from routes.virements import virements_bp
from routes.approvals import approvals_bp
from routes.prior_approvals import prior_approvals_bp
from routes.effort import effort_bp
from routes.milestones import milestones_bp
from routes.tranches import tranches_bp
from routes.amendments import amendments_bp
from routes.assets import assets_bp
from routes.asset_analytics import analytics_bp
from routes.asset_reporting import reporting_bp
from routes.asset_documents import documents_bp as asset_documents_bp
from routes.asset_audit import audit_bp
from routes.asset_forecasting import forecasting_bp
from routes.asset_performance import performance_bp
from routes.asset_barcodes import barcodes_bp
from routes.asset_export_import import export_import_bp
from routes.asset_assignments import asset_assignments_bp
from routes.milestone_kpis import milestone_kpis_bp
from routes.grant_kpis import grant_kpis_bp
from routes.asset_conflicts import asset_conflicts_bp
from routes.asset_checkout import asset_checkout_bp
from routes.milestone_dashboard import milestone_dashboard_bp
from routes.closeout import closeout_bp
from routes.calendar import calendar_bp
from routes.extensions import extensions_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'pagms-mubas-secret-2025-change-in-production'
    app.config['SECRET_KEY'] = app.secret_key
    
    app.config.update(
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_NAME='pagms_session'
    )
    
    # Enable CORS with credentials support - consolidated
    CORS(app, 
         resources={r"/api/*": {
             "origins": [
                 "http://localhost:5173", 
                 "http://127.0.0.1:5173", 
                 "http://localhost:5000", 
                 "http://127.0.0.1:5000"
             ],
             "supports_credentials": True,
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
         }})
    
    # Global Error Handler to capture 500s and add CORS headers
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP errors (like 401, 404, etc.)
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return jsonify({'error': e.description}), e.code
        
        # Log unhandled exceptions with full traceback
        app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'details': str(e)
        }), 500
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'pagms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(grants_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')
    app.register_blueprint(tasks_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(expenses_bp, url_prefix='/api')
    app.register_blueprint(finance_bp, url_prefix='/api')
    app.register_blueprint(documents_bp, url_prefix='/api')
    app.register_blueprint(rules_bp, url_prefix='/api')
    app.register_blueprint(virements_bp, url_prefix='/api')
    app.register_blueprint(approvals_bp, url_prefix='/api')
    app.register_blueprint(prior_approvals_bp, url_prefix='/api')
    app.register_blueprint(effort_bp, url_prefix='/api')
    app.register_blueprint(milestones_bp, url_prefix='/api')
    app.register_blueprint(tranches_bp, url_prefix='/api')
    app.register_blueprint(amendments_bp)
    app.register_blueprint(assets_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(reporting_bp, url_prefix='/api')
    app.register_blueprint(asset_documents_bp, url_prefix='/api')
    app.register_blueprint(audit_bp, url_prefix='/api')
    app.register_blueprint(forecasting_bp, url_prefix='/api')
    app.register_blueprint(performance_bp, url_prefix='/api')
    app.register_blueprint(barcodes_bp, url_prefix='/api')
    app.register_blueprint(export_import_bp, url_prefix='/api')
    app.register_blueprint(asset_assignments_bp, url_prefix='/api')
    app.register_blueprint(milestone_kpis_bp, url_prefix='/api')
    app.register_blueprint(grant_kpis_bp, url_prefix='/api')
    app.register_blueprint(asset_conflicts_bp, url_prefix='/api')
    app.register_blueprint(asset_checkout_bp, url_prefix='/api')
    app.register_blueprint(milestone_dashboard_bp, url_prefix='/api')
    app.register_blueprint(closeout_bp, url_prefix='/api')
    app.register_blueprint(calendar_bp, url_prefix='/api')
    app.register_blueprint(extensions_bp, url_prefix='/api/extensions')

    @app.route('/api/uploads/<path:filename>')
    def serve_uploads(filename):
        uploads_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(uploads_dir, filename)

    @app.route('/health')
    def health_check():
        return {"status": "ok", "message": "PAGMS Backend ili mushe"}, 200

    # Ensure DB is setup on every startup
    setup_database(app)

    return app

def setup_database(app):
    """Utility to provision DB schema and seed initial data."""
    with app.app_context():
        # 1. Ensure instance path exists
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)

        # 2. Create all tables that don't exist
        db.create_all()
        
        # 3. Patch existing tables with new columns (safely)
        import sqlite3
        db_path = os.path.join(app.instance_path, 'pagms.db')
        if not os.path.exists(db_path):
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updates = [
            ("expense_claims", "expense_date", "DATE"),
            ("expense_claims", "description", "TEXT"),
            ("expense_claims", "receipt_filename", "VARCHAR(200)"),
            ("expense_claims", "payment_method", "VARCHAR(50)"),
            ("rule_profiles", "created_at", "DATETIME"),
            ("rule_profiles", "funder_id", "VARCHAR(100)"),
            ("rules", "priority_level", "INTEGER"),
            ("rules", "guidance_text", "TEXT"),
            ("rules", "is_active", "BOOLEAN"),
            ("rules", "created_at", "DATETIME"),
            ("grants", "funder_id", "INTEGER"),
            ("grants", "rule_profile_id", "INTEGER"),
            ("grants", "rule_snapshot_id", "INTEGER"),
            ("grants", "reporting_template_filename", "VARCHAR(200)"),
            ("grants", "indirect_cost_rate", "FLOAT"),
            ("grants", "archive_hash", "VARCHAR(64)"),
            ("grants", "archived_at", "DATETIME"),
            ("rule_profiles", "reporting_template_filename", "VARCHAR(200)"),
            ("budget_categories", "encumbered", "FLOAT"),
            # Rule Evaluation columns
            ("rule_evaluations", "triggered_outcome", "VARCHAR(50)"),
            ("rule_evaluations", "final_outcome", "VARCHAR(50)"),
            ("rule_evaluations", "action_type", "VARCHAR(50)"),
            ("rule_evaluations", "context_snapshot", "TEXT"),
            ("rule_evaluations", "resolved_by_id", "INTEGER"),
            ("rule_evaluations", "resolved_at", "DATETIME"),
            ("rule_evaluations", "resolution_outcome", "VARCHAR(50)"),
            ("rule_evaluations", "override_justification", "TEXT"),
            ("rule_evaluations", "override_cosigned_by", "INTEGER"),
            # Rule Profile Snapshot columns
            ("rule_profile_snapshots", "profile_id", "INTEGER"),
            ("rule_profile_snapshots", "snapshot_data", "TEXT"),
            ("rule_profile_snapshots", "created_by_id", "INTEGER"),
            ("rule_profile_snapshots", "created_at", "DATETIME"),
            # Budget Virement columns
            ("budget_virements", "virement_number", "VARCHAR(50)"),
            ("budget_virements", "grant_id", "INTEGER"),
            ("budget_virements", "reason", "TEXT"),
            ("budget_virements", "total_amount", "FLOAT"),
            ("budget_virements", "requested_by_id", "INTEGER"),
            ("budget_virements", "requested_at", "DATETIME"),
            ("budget_virements", "status", "VARCHAR(20)"),
            ("budget_virements", "current_step_id", "INTEGER"),
            # Milestone additions
            ("milestones", "evidence_filename", "VARCHAR(200)"),
            ("milestones", "reporting_period", "VARCHAR(100)"),
            ("milestones", "triggers_tranche", "INTEGER"),
            # Rule Evaluation additions
            ("rule_evaluations", "triggered_outcome", "TEXT"),
            # Prior Approval Request additions
            ("prior_approval_requests", "category", "TEXT"),
            ("prior_approval_requests", "amount", "FLOAT"),
            ("prior_approval_requests", "workflow_id", "INTEGER"),
            # Expense Claim additions
            ("expense_claims", "prior_approval_id", "INTEGER"),
            # Deliverable Submission additions
            ("deliverable_submissions", "user_id", "INTEGER"),
            ("deliverable_submissions", "file_path", "VARCHAR(500)"),
            ("deliverable_submissions", "hours_worked", "FLOAT"),
            ("deliverable_submissions", "activity_notes", "TEXT"),
            ("deliverable_submissions", "photo_path", "VARCHAR(200)"),
            ("deliverable_submissions", "document_paths", "TEXT"),
            ("deliverable_submissions", "gps_coordinates", "VARCHAR(50)"),
            ("deliverable_submissions", "submitted_at", "DATETIME"),
            ("deliverable_submissions", "verification_status", "VARCHAR(20)"),
            # Effort Certification additions
            ("effort_certifications", "grant_id", "INTEGER"),
            ("effort_certifications", "period_month", "INTEGER"),
            ("effort_certifications", "period_year", "INTEGER"),
            ("effort_certifications", "logged_hours", "FLOAT"),
            ("effort_certifications", "certified_percentage", "FLOAT"),
            ("effort_certifications", "signature_text", "VARCHAR(100)"),
            ("effort_certifications", "ip_address", "VARCHAR(45)"),
            ("effort_certifications", "certified_at", "DATETIME"),
            ("effort_certifications", "status", "VARCHAR(20)"),
            ("effort_certifications", "is_pi_certification", "BOOLEAN"),
            ("effort_certifications", "is_rsu_overridden", "BOOLEAN"),
            ("effort_certifications", "override_justification", "TEXT"),
            # Co-PI additions
            ("grant_team", "budget_authority", "BOOLEAN DEFAULT 0"),
            ("approval_workflows", "grant_id", "INTEGER"),
            # Enhanced Tranche System additions
            ("tranches", "tranche_number", "INTEGER"),
            ("tranches", "currency", "VARCHAR(3) DEFAULT 'USD'"),
            ("tranches", "description", "VARCHAR(200)"),
            ("tranches", "trigger_type", "VARCHAR(20) DEFAULT 'milestone'"),
            ("tranches", "triggering_milestone_id", "INTEGER"),
            ("tranches", "required_report_type", "VARCHAR(50)"),
            ("tranches", "trigger_date", "DATE"),
            ("tranches", "released_at", "DATETIME"),
            ("tranches", "released_by", "INTEGER"),
            ("tranches", "version", "INTEGER DEFAULT 1"),
            ("tranches", "parent_tranche_id", "INTEGER"),
            ("tranches", "amendment_reason", "TEXT"),
            ("tranches", "amendment_approved_by", "INTEGER"),
            ("tranches", "amendment_approved_at", "DATETIME"),
            ("tranches", "updated_at", "DATETIME"),  # SQLite ALTER doesn't support DEFAULT CURRENT_TIMESTAMP
            # Ethics Compliance additions
            ("grants", "ethics_required", "BOOLEAN DEFAULT 0"),
            ("grants", "ethics_status", "VARCHAR(30) DEFAULT 'NOT_SUBMITTED'"),
            ("grants", "ethics_expiry_date", "DATE"),
            ("grants", "ethics_approval_number", "VARCHAR(100)"),
        ]
        
        patched = False
        for table_name, col_name, col_type in updates:
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_info = cursor.fetchall()
                if table_info: # Table exists
                    cols = [c[1] for c in table_info]
                    if col_name not in cols:
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                        patched = True
            except Exception as e:
                # Column likely exists or table doesn't
                pass

        # --- Fix rule_profile_rules association table names ---
        try:
            cursor.execute("PRAGMA table_info(rule_profile_rules)")
            table_info = cursor.fetchall()
            if table_info:
                rpr_cols = [c[1] for c in table_info]
                if 'profile_id' not in rpr_cols:
                    cursor.execute("DROP TABLE rule_profile_rules")
                    patched = True
        except Exception as e:
            pass
        
        if patched:
            conn.commit()
            
            # Update existing tranches with tranche numbers
            try:
                cursor.execute("""
                    UPDATE tranches 
                    SET tranche_number = (
                        SELECT row_num 
                        FROM (
                            SELECT id, ROW_NUMBER() OVER (PARTITION BY grant_id ORDER BY expected_date, id) as row_num 
                            FROM tranches
                        ) ranked 
                        WHERE ranked.id = tranches.id
                    )
                    WHERE tranche_number IS NULL
                """)
                conn.commit()
                print("✅ Updated existing tranches with tranche numbers")
            except Exception as e:
                print(f"⚠️  Error updating tranche numbers: {e}")
                
        conn.close()

        # 4. Optional Seeding (Seed only if users table is empty)
        try:
            from models import User, Grant, BudgetCategory, Milestone
            import datetime
            if User.query.count() == 0:
                from services.auth_service import AuthService
                pi = AuthService.create_user('Dr. PI', 'pi@mubas.ac.mw', 'PI', 'mubas123')
                AuthService.create_user('Admin RSU', 'admin@mubas.ac.mw', 'RSU', 'mubas123')
                
                # Seed a sample grant for Dr. PI
                g = Grant(
                    title="MUBAS Smart Irrigation Research",
                    funder="NERC",
                    grant_code="MUBAS-SIR-2025",
                    start_date=datetime.date(2025, 1, 1),
                    end_date=datetime.date(2027, 12, 31),
                    total_budget=500000.0,
                    pi_id=pi.id,
                    status="active"
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
                print("✅ Seeded initial PI, RSU and Sample Grant")
        except Exception as e:
            print(f"Seeding error: {e}")
            db.session.rollback()

# Global App Instance for compatibility with 'flask run'
app = create_app()

if __name__ == '__main__':
    # setup_database(app) is now called inside create_app()
    app.run(debug=True, port=5000)