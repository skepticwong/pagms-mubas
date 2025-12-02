from flask import Blueprint, request, jsonify, session, send_from_directory
from flask_cors import CORS
from models import db, AuditLog, Grant
from services.report_service import ReportService
import os

reports_bp = Blueprint('reports', __name__)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

@reports_bp.route('/grants/<int:grant_id>/reporting-options', methods=['GET'])
def get_reporting_options(grant_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        options = ReportService.get_reporting_options(grant_id)
        return jsonify(options), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/grants/<int:grant_id>/generate-report', methods=['POST'])
def generate_report(grant_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    report_type = data.get('type')  # e.g., Annual
    report_value = data.get('value') # e.g., 2026

    if not report_type or not report_value:
        return jsonify({'error': 'Missing report type or value'}), 400

    try:
        # Compile data
        report_data = ReportService.compile_report_data(grant_id, report_type, report_value)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{grant_id}_{report_type}_{report_value}_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)
        
        # Generate PDF
        ReportService.generate_pdf_report(report_data, filepath)
        
        # Audit Log
        grant = Grant.query.get(grant_id)
        audit_log = AuditLog(
            user_id=user_id,
            action='report_generated',
            resource_type='grant',
            resource_id=grant_id,
            details=f'PI generated {report_type} Report for period {report_value} on grant "{grant.title}"'
        )
        db.session.add(audit_log)
        db.session.commit()

        # Build URLs (frontend will use these)
        # Assuming app serves static from /uploads/reports
        download_url = f"http://localhost:5000/api/reports/download/{filename}"
        preview_url = f"http://localhost:5000/api/reports/preview/{filename}"

        return jsonify({
            'message': 'Report generated successfully',
            'download_url': download_url,
            'preview_url': preview_url
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Report generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/download/<filename>', methods=['GET'])
def download_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)

@reports_bp.route('/reports/preview/<filename>', methods=['GET'])
def preview_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=False)

# Helper for datetime needed in generate_report
from datetime import datetime
