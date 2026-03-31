"""
Tranche Management API Routes
Phase 3: API endpoints for tranche amendment workflow with business rules integration
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import json

# Import models carefully to avoid circular imports
from models import db, Tranche, Grant

tranches_bp = Blueprint('tranches', __name__)

@tranches_bp.route('/grants/<int:grant_id>/tranches', methods=['GET'])
def get_grant_tranches(grant_id):
    """
    Get all tranches for a specific grant with amendment history
    Returns: tranche data with amounts, dates, status, and trigger information
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Get all tranches for this grant (excluding archived), ordered by tranche number
        tranches = Tranche.query.filter(
            Tranche.grant_id == grant_id,
            Tranche.status != 'archived'
        ).order_by(Tranche.tranche_number.asc().nullslast()).all()
        
        # Add tranche_number for UI (1-based index) and include amendment history
        results = []
        for tranche in tranches:
            tranche_dict = tranche.to_dict(include_amendments=True)
            results.append(tranche_dict)
        
        return jsonify(results), 200
    except Exception as e:
        print(f"Error fetching tranches: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch tranches', 'details': str(e)}), 500

@tranches_bp.route('/tranches/<int:tranche_id>/amendments', methods=['POST'])
def submit_tranche_amendment(tranche_id):
    """
    Submit a tranche amendment request
    Returns: success/failure with validation errors if any
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        tranche = Tranche.query.get(tranche_id)
        if not tranche:
            return jsonify({'error': 'Tranche not found'}), 404
        
        data = request.get_json()
        
        # Import services locally to avoid circular imports
        from services.tranche_amendment_service import TrancheAmendmentService
        
        # Use the amendment service for business logic
        result = TrancheAmendmentService.submit_amendment(
            user_id=user_id,
            grant_id=tranche.grant_id,
            tranche_id=tranche_id,
            amendment_data=data
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        print(f"Error submitting amendment: {str(e)}")
        return jsonify({'error': 'Failed to submit amendment', 'details': str(e)}), 500

@tranches_bp.route('/amendments/<int:amendment_id>/approve', methods=['POST'])
def approve_tranche_amendment(amendment_id):
    """
    Approve a tranche amendment and apply the changes
    Returns: success/failure with updated tranche data
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Import services locally to avoid circular imports
        from services.tranche_amendment_service import TrancheAmendmentService
        
        # Use the amendment service for business logic
        result = TrancheAmendmentService.approve_amendment(
            approver_id=user_id,
            amendment_id=amendment_id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        print(f"Error approving amendment: {str(e)}")
        return jsonify({'error': 'Failed to approve amendment', 'details': str(e)}), 500

@tranches_bp.route('/amendments/<int:amendment_id>/reject', methods=['POST'])
def reject_tranche_amendment(amendment_id):
    """
    Reject a tranche amendment
    Returns: success/failure
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        amendment = TrancheAmendment.query.get(amendment_id)
        if not amendment:
            return jsonify({'error': 'Amendment not found'}), 404
        
        if amendment.status != 'pending':
            return jsonify({'error': 'Amendment already processed'}), 400
        
        data = request.get_json()
        rejection_reason = data.get('rejection_reason', '')
        
        # Update amendment status
        amendment.status = 'rejected'
        amendment.approved_by = user_id
        amendment.approved_at = datetime.utcnow()
        amendment.rejection_reason = rejection_reason
        
        # Create audit log
        from models import AuditLog
        db.session.add(AuditLog(
            user_id=user_id,
            action='tranche_amendment_rejected',
            resource_type='tranche_amendment',
            resource_id=amendment.id,
            details=f'Tranche amendment rejected: {rejection_reason[:100]}...'
        ))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Amendment rejected successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting amendment: {str(e)}")
        return jsonify({'error': 'Failed to reject amendment', 'details': str(e)}), 500

@tranches_bp.route('/tranches/<int:tranche_id>/amendments', methods=['GET'])
def get_tranche_amendments(tranche_id):
    """
    Get amendment history for a specific tranche
    Returns: list of amendment records
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        tranche = Tranche.query.get(tranche_id)
        if not tranche:
            return jsonify({'error': 'Tranche not found'}), 404
        
        amendments = TrancheAmendment.query.filter_by(tranche_id=tranche_id).order_by(
            TrancheAmendment.created_at.desc()
        ).all()
        
        results = [amendment.to_dict() for amendment in amendments]
        
        return jsonify(results), 200
        
    except Exception as e:
        print(f"Error fetching amendment history: {str(e)}")
        return jsonify({'error': 'Failed to fetch amendment history', 'details': str(e)}), 500

@tranches_bp.route('/grants/<int:grant_id>/tranches/validate', methods=['POST'])
def validate_tranche_changes(grant_id):
    """
    Validate proposed tranche changes before submission
    Returns: validation errors or success
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        tranche_id = data.get('tranche_id')
        changes = data.get('changes', {})
        
        if tranche_id:
            # Validate amendment
            errors = TrancheValidationService.validate_tranche_amendment(grant_id, tranche_id, changes)
        else:
            # Validate new tranche
            errors = TrancheValidationService.validate_new_tranche(grant_id, changes)
        
        if errors:
            return jsonify({
                'valid': False,
                'errors': errors
            }), 200
        else:
            return jsonify({
                'valid': True,
                'message': 'Changes are valid'
            }), 200
        
    except Exception as e:
        print(f"Error validating tranche changes: {str(e)}")
        return jsonify({'error': 'Validation failed', 'details': str(e)}), 500

@tranches_bp.route('/tranches/<int:tranche_id>/release-check', methods=['GET'])
def check_tranche_release_readiness(tranche_id):
    """
    Check if a tranche is ready for release based on its trigger
    Returns: readiness status and trigger details
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Import services locally to avoid circular imports
        from services.tranche_amendment_service import TrancheReleaseService
        
        result = TrancheReleaseService.check_tranche_release_readiness(tranche_id)
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error checking tranche release readiness: {str(e)}")
        return jsonify({'error': 'Failed to check release readiness', 'details': str(e)}), 500

@tranches_bp.route('/tranches/<int:tranche_id>/release', methods=['POST'])
def release_tranche(tranche_id):
    """
    Release a tranche (manual release or when ready)
    Returns: success/failure with release details
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json() or {}
        
        # Import services locally to avoid circular imports
        from services.tranche_amendment_service import TrancheReleaseService
        
        result = TrancheReleaseService.release_tranche(
            tranche_id=tranche_id,
            released_by_user_id=user_id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        print(f"Error releasing tranche: {str(e)}")
        return jsonify({'error': 'Failed to release tranche', 'details': str(e)}), 500

@tranches_bp.route('/amendments/pending', methods=['GET'])
def get_pending_amendments():
    """
    Get all pending tranche amendments for approval
    Returns: list of pending amendment records
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Import services locally to avoid circular imports
        from services.tranche_amendment_service import TrancheAmendmentService
        
        amendments = TrancheAmendmentService.get_pending_amendments()
        return jsonify(amendments), 200
        
    except Exception as e:
        print(f"Error fetching pending amendments: {str(e)}")
        return jsonify({'error': 'Failed to fetch pending amendments', 'details': str(e)}), 500
