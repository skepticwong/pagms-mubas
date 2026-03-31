from flask import Blueprint, request, jsonify, session
from models import db, Milestone, Grant
from services.milestone_service import MilestoneService
from datetime import datetime

milestones_bp = Blueprint('milestones', __name__)

@milestones_bp.route('/grants/<int:grant_id>/milestones', methods=['GET'])
def get_grant_milestones(grant_id):
    milestones = MilestoneService.get_milestones_by_grant(grant_id)
    return jsonify([m.to_dict() for m in milestones]), 200

@milestones_bp.route('/milestones', methods=['POST'])
def create_milestone():
    data = request.json
    try:
        new_milestone = Milestone(
            grant_id=data['grant_id'],
            title=data['title'],
            description=data.get('description'),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d') if data.get('due_date') else None,
            status=data.get('status', 'NOT_STARTED'),
            triggers_tranche=data.get('triggers_tranche'),
            sequence=data.get('sequence', 0)
        )
        db.session.add(new_milestone)
        db.session.commit()
        return jsonify(new_milestone.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@milestones_bp.route('/milestones/<int:id>', methods=['GET'])
def get_milestone(id):
    milestone = MilestoneService.get_milestone_details(id)
    if not milestone:
        return jsonify({'error': 'Milestone not found'}), 404
    return jsonify(milestone), 200

@milestones_bp.route('/milestones/<int:id>', methods=['PUT'])
def update_milestone(id):
    milestone = Milestone.query.get_or_404(id)
    data = request.json
    try:
        if 'title' in data: milestone.title = data['title']
        if 'description' in data: milestone.description = data['description']
        if 'status' in data: 
            milestone.status = data['status']
            if milestone.status == 'COMPLETED' and not milestone.completion_date:
                milestone.completion_date = datetime.utcnow()
        if 'due_date' in data: 
            milestone.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d') if data['due_date'] else None
        if 'triggers_tranche' in data: milestone.triggers_tranche = data['triggers_tranche']
        if 'sequence' in data: milestone.sequence = data['sequence']
        
        db.session.commit()
        
        # Trigger status check logic (in case tasks/deliverables affect it)
        MilestoneService.update_milestone_status(id)
        
        return jsonify(milestone.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@milestones_bp.route('/milestones/<int:id>', methods=['DELETE'])
def delete_milestone(id):
    milestone = Milestone.query.get_or_404(id)
    db.session.delete(milestone)
    db.session.commit()
    return jsonify({'message': 'Milestone deleted'}), 200
