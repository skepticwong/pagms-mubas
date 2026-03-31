# backend/routes/extensions.py
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from models import db, Grant, NoCostExtension, User, AuditLog, Document
from services.grant_service import GrantService
from services.audit_service import AuditService

extensions_bp = Blueprint('extensions', __name__)

@extensions_bp.route('/request', methods=['POST'])
def request_extension():
    """
    PI requests a No-Cost Extension.
    Expects multipart form with:
    - grant_id
    - current_end_date
    - requested_end_date
    - justification
    - funder_approval_doc (Optional File)
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role not in ['PI', 'Co-PI']:
        return jsonify({'error': 'Only PIs can request extensions'}), 403

    grant_id = request.form.get('grant_id')
    requested_end_date_str = request.form.get('requested_end_date')
    justification = request.form.get('justification')

    if not grant_id or not requested_end_date_str or not justification:
        return jsonify({'error': 'Missing required fields'}), 400

    grant = Grant.query.get(grant_id)
    if not grant:
        return jsonify({'error': 'Grant not found'}), 404

    # Save funder letter if provided
    doc_id = None
    funder_file = request.files.get('funder_approval_doc')
    if funder_file:
        filename = GrantService._save_file(funder_file, 'NCE_Approval_Letters')
        doc = Document(
            grant_id=grant.id,
            uploader_id=user_id,
            file_name=funder_file.filename,
            file_path=filename,
            doc_type='NCE_Approval'
        )
        db.session.add(doc)
        db.session.flush()
        doc_id = doc.id

    extension = NoCostExtension(
        grant_id=grant.id,
        requester_id=user_id,
        current_end_date=grant.end_date,
        requested_end_date=datetime.strptime(requested_end_date_str, '%Y-%m-%d').date(),
        justification=justification,
        document_id=doc_id,
        status='pending'
    )

    db.session.add(extension)
    db.session.commit()

    return jsonify(extension.to_dict()), 201

@extensions_bp.route('/pending', methods=['GET'])
def list_pending_extensions():
    """RSU view of all pending NCEs."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Only RSU can view pending extensions'}), 403

    pending = NoCostExtension.query.filter_by(status='pending').all()
    
    results = []
    for ext in pending:
        data = ext.to_dict()
        data['grant_title'] = ext.grant.title
        data['grant_code'] = ext.grant.grant_code
        results.append(data)

    return jsonify({'extensions': results}), 200

@extensions_bp.route('/<int:extension_id>/resolve', methods=['PUT'])
def resolve_extension(extension_id):
    """RSU approves or rejects an NCE."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or user.role != 'RSU':
        return jsonify({'error': 'Only RSU can resolve extensions'}), 403

    ext = NoCostExtension.query.get(extension_id)
    if not ext:
        return jsonify({'error': 'Extension request not found'}), 404

    data = request.json
    status = data.get('status') # 'approved' or 'rejected'
    notes = data.get('notes')

    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    ext.status = status
    ext.resolver_id = user_id
    ext.resolved_at = datetime.utcnow()
    ext.resolver_notes = notes

    if status == 'approved':
        # APPLY THE CASCADE
        try:
            GrantService.apply_extension(ext.grant_id, ext.requested_end_date.strftime('%Y-%m-%d'), user_id)
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f"Failed to apply extension: {str(e)}"}), 500

    db.session.commit()
    return jsonify(ext.to_dict()), 200

@extensions_bp.route('/grant/<int:grant_id>', methods=['GET'])
def get_grant_extensions(grant_id):
    """History of extensions for a specific grant."""
    exts = NoCostExtension.query.filter_by(grant_id=grant_id).order_by(NoCostExtension.created_at.desc()).all()
    return jsonify({'extensions': [e.to_dict() for e in exts]}), 200
