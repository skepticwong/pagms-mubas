from flask import Blueprint, request, jsonify, session
from services.virement_service import VirementService
from models import User

virements_bp = Blueprint('virements', __name__)
virement_service = VirementService()

@virements_bp.route('/virements/request', methods=['POST'])
def request_virement():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    try:
        virement = virement_service.create_virement_request(
            grant_id=data['grant_id'],
            from_category_id=data['from_category_id'],
            to_category_id=data['to_category_id'],
            amount=data['amount'],
            justification=data.get('justification', ''),
            user_id=user_id
        )
        return jsonify({
            'message': 'Virement request processed',
            'status': virement.status,
            'virement_id': virement.id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@virements_bp.route('/virements/grant/<int:grant_id>', methods=['GET'])
def list_virements(grant_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    virements = virement_service.list_virements_for_grant(grant_id)
    return jsonify([v.to_dict() for v in virements]), 200

@virements_bp.route('/virements/<int:virement_id>/approve', methods=['POST'])
def approve_virement(virement_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if user.role not in ['RSU', 'Finance']:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        virement = virement_service.approve_virement(virement_id, user_id)
        return jsonify({'message': 'Virement approved', 'status': virement.status}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@virements_bp.route('/virements/<int:virement_id>/reject', methods=['POST'])
def reject_virement(virement_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if user.role not in ['RSU', 'Finance']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    try:
        virement = virement_service.reject_virement(virement_id, user_id, data.get('comment'))
        return jsonify({'message': 'Virement rejected', 'status': virement.status}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
