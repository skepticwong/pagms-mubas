from flask import Blueprint, send_file, jsonify, session
import os
from models import User
from services.audit_service import AuditService

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/rsu/audit-package/<int:grant_id>', methods=['GET'])
def download_audit_package(grant_id):
    """
    Triggers ZIP generation for a grant and downloads it.
    RSU only.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        zip_path = AuditService.generate_audit_package(grant_id)
        
        if not os.path.exists(zip_path):
            return jsonify({'error': 'Failed to generate audit package'}), 500
            
        return send_file(zip_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': f"Audit package failed: {str(e)}"}), 500
