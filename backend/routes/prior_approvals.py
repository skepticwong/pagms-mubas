from flask import Blueprint, request, jsonify
from services.prior_approval_service import PriorApprovalService
from middleware import token_required

prior_approvals_bp = Blueprint('prior_approvals', __name__)
prior_approval_service = PriorApprovalService()

@prior_approvals_bp.route('/prior-approvals/grant/<int:grant_id>', methods=['GET'])
@token_required
def get_grant_prior_approvals(user, grant_id):
    requests = prior_approval_service.get_requests_for_grant(grant_id)
    return jsonify([req.to_dict() for req in requests]), 200

@prior_approvals_bp.route('/prior-approvals/request', methods=['POST'])
@token_required
def create_prior_approval_request(user):
    data = request.json
    try:
        req, evaluation = prior_approval_service.create_request(
            grant_id=data['grant_id'],
            requester_id=user.id,
            request_type=data['request_type'],
            category=data['category'],
            amount=data['amount'],
            justification=data['justification']
        )
        return jsonify({
            'message': 'Prior approval request created',
            'request': req.to_dict(),
            'evaluation': evaluation
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
