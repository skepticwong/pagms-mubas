import os
import traceback
from datetime import datetime
from flask import Blueprint, jsonify, session, send_file
from services.closeout_service import get_closeout_status, lock_grant_archive, generate_final_report
from services.report_service import ReportService

closeout_bp = Blueprint('closeout', __name__)

@closeout_bp.route('/grants/<int:grant_id>/closeout-status', methods=['GET'])
def fetch_closeout_status(grant_id):
    """
    Returns the 4-gate compliance check for grant closeout.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        status_data = get_closeout_status(grant_id)
        if not status_data:
            return jsonify({'error': 'Grant not found'}), 404
            
        return jsonify(status_data), 200
        
    except Exception as e:
        print(f"Error fetching closeout status: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to process closeout status', 'details': str(e)}), 500

@closeout_bp.route('/grants/<int:grant_id>/lock-archive', methods=['POST'])
def execute_lock_archive(grant_id):
    """
    Locks and archives the grant if all 4 gates are compliant.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    try:
        result = lock_grant_archive(grant_id, user_id)
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error locking archive: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to lock archive', 'details': str(e)}), 500

@closeout_bp.route('/grants/<int:grant_id>/final-report', methods=['GET'])
def get_final_report(grant_id):
    """
    Returns the auto-generated Final Report dossier for the grant.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from models import Grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
            
        report_data = generate_final_report(grant_id)
        return jsonify({
            'report': report_data,
            'archive_hash': grant.archive_hash,
            'archived_at': grant.archived_at.isoformat() if grant.archived_at else None
        }), 200
    except Exception as e:
        print(f"Error fetching final report: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to fetch final report', 'details': str(e)}), 500

@closeout_bp.route('/grants/<int:grant_id>/download-dossier', methods=['GET'])
def download_dossier(grant_id):
    """
    Generates and downloads the final closeout dossier PDF.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    try:
        from models import Grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
            
        # Create uploads directory if not exists
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'closeouts')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        filename = f"Closeout_Dossier_{grant.grant_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(upload_dir, filename)
        
        ReportService.generate_closeout_dossier_pdf(grant_id, filepath)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"Error downloading dossier: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to generate dossier PDF', 'details': str(e)}), 500
