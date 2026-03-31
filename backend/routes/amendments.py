"""
Amendments Routes - API endpoints for No-Cost Extension (NCE) workflow
Handles extension requests, approvals, and amendment management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, GrantAmendment, Grant, User
from services.nce_service import NCEService
from middleware import token_required, rsu_required

amendments_bp = Blueprint('amendments', __name__)

@amendments_bp.route('/nce/request', methods=['POST'])
@token_required
def request_nce(user):
    """
    Submit a new No-Cost Extension request
    
    Request Body:
    {
        "grant_id": 1,
        "requested_end_date": "2025-03-31",
        "justification": "Research delayed due to equipment shipping delays",
        "supporting_docs": ["doc1.pdf", "doc2.pdf"]
    }
    """
    data = request.json
    grant_id = data.get('grant_id')
    requested_end_date = data.get('requested_end_date')
    justification = data.get('justification')
    supporting_docs = data.get('supporting_docs', [])
    
    # Validation
    if not all([grant_id, requested_end_date, justification]):
        return jsonify({
            'error': 'Missing required fields',
            'required': ['grant_id', 'requested_end_date', 'justification']
        }), 400
    
    if not isinstance(supporting_docs, list):
        return jsonify({'error': 'supporting_docs must be an array'}), 400
    
    try:
        result = NCEService.request_extension(
            grant_id, requested_end_date, justification, user.id, supporting_docs
        )
        
        if result['success']:
            return jsonify({
                'message': 'Extension request submitted successfully',
                'amendment': result['amendment'],
                'rule_evaluation': result.get('rule_evaluation'),
                'warnings': result.get('warnings', [])
            }), 201
        else:
            return jsonify({
                'error': 'Extension request validation failed',
                'errors': result['errors'],
                'warnings': result.get('warnings', [])
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to submit extension request: {str(e)}'}), 500

@amendments_bp.route('/nce/<int:amendment_id>/approve', methods=['POST'])
@token_required
@rsu_required
def approve_nce(user, amendment_id):
    """
    Approve an NCE request
    
    Request Body:
    {
        "notes": "Approved based on funder email confirmation",
        "shift_milestones": true
    }
    """
    amendment = GrantAmendment.query.get_or_404(amendment_id)
    
    if amendment.status != 'PENDING':
        return jsonify({'error': 'Amendment is not in pending status'}), 400
    
    data = request.json
    notes = data.get('notes', '')
    shift_milestones = data.get('shift_milestones', True)
    
    try:
        result = NCEService.approve_extension(
            amendment_id, user.id, notes, shift_milestones
        )
        
        if result['success']:
            return jsonify({
                'message': 'Extension request approved successfully',
                'amendment': result['amendment'],
                'grant': result['grant'],
                'approved_by': user.name,
                'approved_at': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to approve extension request: {str(e)}'}), 500

@amendments_bp.route('/nce/<int:amendment_id>/reject', methods=['POST'])
@token_required
@rsu_required
def reject_nce(user, amendment_id):
    """
    Reject an NCE request
    
    Request Body:
    {
        "rejection_reason": "Extension period exceeds funder policy limits"
    }
    """
    amendment = GrantAmendment.query.get_or_404(amendment_id)
    
    if amendment.status != 'PENDING':
        return jsonify({'error': 'Amendment is not in pending status'}), 400
    
    data = request.json
    rejection_reason = data.get('rejection_reason', '')
    
    if not rejection_reason:
        return jsonify({'error': 'rejection_reason is required'}), 400
    
    try:
        result = NCEService.reject_extension(amendment_id, user.id, rejection_reason)
        
        if result['success']:
            return jsonify({
                'message': 'Extension request rejected successfully',
                'amendment': result['amendment'],
                'rejected_by': user.name,
                'rejected_at': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to reject extension request: {str(e)}'}), 500

@amendments_bp.route('/nce/<int:amendment_id>/withdraw', methods=['POST'])
@token_required
def withdraw_nce(user, amendment_id):
    """
    Withdraw a pending NCE request (only by requester)
    """
    try:
        result = NCEService.withdraw_request(amendment_id, user.id)
        
        if result['success']:
            return jsonify({
                'message': 'Extension request withdrawn successfully',
                'amendment': result['amendment'],
                'withdrawn_by': user.name,
                'withdrawn_at': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to withdraw extension request: {str(e)}'}), 500

@amendments_bp.route('/pending', methods=['GET'])
@token_required
@rsu_required
def get_pending_amendments(user):
    """
    Get all pending amendments for RSU review
    
    Query Parameters:
    - type: Filter by amendment type (NCE, BUDGET_SHIFT, etc.)
    - page: Page number for pagination
    - limit: Number of items per page
    """
    amendment_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    try:
        amendments = NCEService.get_pending_amendments()
        
        # Filter by type if specified
        if amendment_type:
            amendments = [a for a in amendments if a.amendment_type == amendment_type]
        
        # Pagination
        total = len(amendments)
        start = (page - 1) * limit
        end = start + limit
        paginated_amendments = amendments[start:end]
        
        # Add additional context
        amendments_data = []
        for amendment in paginated_amendments:
            amendment_dict = amendment.to_dict()
            
            # Add grant information
            grant = amendment.grant
            amendment_dict['grant'] = {
                'id': grant.id,
                'title': grant.title,
                'pi_name': grant.pi.name if grant.pi else 'Unknown',
                'current_end_date': grant.end_date.isoformat() if grant.end_date else None
            }
            
            # Add requester information
            requester = amendment.requester
            amendment_dict['requester'] = {
                'id': requester.id,
                'name': requester.name,
                'email': requester.email
            } if requester else None
            
            amendments_data.append(amendment_dict)
        
        return jsonify({
            'amendments': amendments_data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch pending amendments: {str(e)}'}), 500

@amendments_bp.route('/grant/<int:grant_id>/amendments', methods=['GET'])
@token_required
def get_grant_amendments(user, grant_id):
    """
    Get all amendments for a specific grant
    
    Query Parameters:
    - type: Filter by amendment type
    - status: Filter by status
    """
    amendment_type = request.args.get('type')
    status = request.args.get('status')
    
    try:
        amendments = NCEService.get_grant_amendments(grant_id)
        
        # Apply filters
        if amendment_type:
            amendments = [a for a in amendments if a.amendment_type == amendment_type]
        
        if status:
            amendments = [a for a in amendments if a.status == status]
        
        # Add context information
        amendments_data = []
        for amendment in amendments:
            amendment_dict = amendment.to_dict()
            
            # Add approver/rejecter information
            if amendment.approved_by:
                approver = User.query.get(amendment.approved_by)
                amendment_dict['approver'] = {
                    'id': approver.id,
                    'name': approver.name
                } if approver else None
            
            if amendment.rejected_by:
                rejecter = User.query.get(amendment.rejected_by)
                amendment_dict['rejecter'] = {
                    'id': rejecter.id,
                    'name': rejecter.name
                } if rejecter else None
            
            amendments_data.append(amendment_dict)
        
        return jsonify({
            'amendments': amendments_data,
            'total': len(amendments)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch grant amendments: {str(e)}'}), 500

@amendments_bp.route('/nce/<int:amendment_id>', methods=['GET'])
@token_required
def get_amendment_details(user, amendment_id):
    """
    Get detailed information about a specific amendment
    """
    try:
        amendment = NCEService.get_amendment_details(amendment_id)
        
        if not amendment:
            return jsonify({'error': 'Amendment not found'}), 404
        
        amendment_dict = amendment.to_dict()
        
        # Add related information
        grant = amendment.grant
        amendment_dict['grant'] = {
            'id': grant.id,
            'title': grant.title,
            'grant_code': grant.grant_code,
            'pi_name': grant.pi.name if grant.pi else 'Unknown',
            'current_end_date': grant.end_date.isoformat() if grant.end_date else None,
            'total_budget': grant.total_budget
        }
        
        # Add user information
        if amendment.requested_by:
            requester = User.query.get(amendment.requested_by)
            amendment_dict['requester'] = {
                'id': requester.id,
                'name': requester.name,
                'email': requester.email,
                'role': requester.role
            } if requester else None
        
        if amendment.approved_by:
            approver = User.query.get(amendment.approved_by)
            amendment_dict['approver'] = {
                'id': approver.id,
                'name': approver.name,
                'role': approver.role
            } if approver else None
        
        if amendment.rejected_by:
            rejecter = User.query.get(amendment.rejected_by)
            amendment_dict['rejecter'] = {
                'id': rejecter.id,
                'name': rejecter.name,
                'role': rejecter.role
            } if rejecter else None
        
        return jsonify(amendment_dict), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch amendment details: {str(e)}'}), 500

@amendments_bp.route('/nce/statistics', methods=['GET'])
@token_required
@rsu_required
def get_extension_statistics(user):
    """
    Get statistics about NCE requests and approvals
    """
    try:
        stats = NCEService.get_extension_statistics()
        
        return jsonify({
            'statistics': stats,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch extension statistics: {str(e)}'}), 500

@amendments_bp.route('/nce/<int:amendment_id>/history', methods=['GET'])
@token_required
def get_amendment_history(user, amendment_id):
    """
    Get the history/audit trail for an amendment
    """
    try:
        amendment = GrantAmendment.query.get_or_404(amendment_id)
        
        history = []
        
        # Request creation
        history.append({
            'action': 'REQUESTED',
            'timestamp': amendment.requested_at.isoformat() if amendment.requested_at else None,
            'user': {
                'id': amendment.requested_by,
                'name': User.query.get(amendment.requested_by).name if User.query.get(amendment.requested_by) else 'Unknown'
            },
            'details': {
                'extension_days': amendment.extension_days,
                'justification': amendment.justification
            }
        })
        
        # Approval
        if amendment.approved_at:
            history.append({
                'action': 'APPROVED',
                'timestamp': amendment.approved_at.isoformat(),
                'user': {
                    'id': amendment.approved_by,
                    'name': User.query.get(amendment.approved_by).name if User.query.get(amendment.approved_by) else 'Unknown'
                },
                'details': {
                    'new_end_date': amendment.requested_new_end_date.isoformat() if amendment.requested_new_end_date else None
                }
            })
        
        # Rejection
        if amendment.rejected_at:
            history.append({
                'action': 'REJECTED',
                'timestamp': amendment.rejected_at.isoformat(),
                'user': {
                    'id': amendment.rejected_by,
                    'name': User.query.get(amendment.rejected_by).name if User.query.get(amendment.rejected_by) else 'Unknown'
                },
                'details': {
                    'rejection_reason': 'See amendment description'
                }
            })
        
        return jsonify({
            'amendment_id': amendment_id,
            'history': history
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch amendment history: {str(e)}'}), 500

# Error handlers
@amendments_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Amendment not found'}), 404

@amendments_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access denied'}), 403

@amendments_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
