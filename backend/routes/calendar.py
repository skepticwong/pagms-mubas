from flask import Blueprint, request, jsonify, session
import models
from sqlalchemy import or_
from datetime import datetime, date
import json

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/events', methods=['GET'])
def get_events():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = models.User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    events = []

    # 1. Manual Calendar Events
    try:
        # Robust grant detection
        grants_as_pi = getattr(user, 'grants_as_pi', [])
        grant_roles = getattr(user, 'grant_roles', [])
        my_grant_ids = [g.id for g in grants_as_pi] + [gt.grant_id for gt in grant_roles]

        manual_events = models.CalendarEvent.query.filter(
            or_(
                models.CalendarEvent.event_type == 'BROADCAST',
                models.CalendarEvent.user_id == user_id,
                (models.CalendarEvent.event_type == 'FINANCE') & (user.role == 'PI'),
                (models.CalendarEvent.grant_id != None) & (models.CalendarEvent.grant_id.in_(my_grant_ids))
            )
        ).all()
        events.extend([e.to_dict() for e in manual_events])
    except Exception as e:
        # Log to stdout for debugging
        print(f"Error fetching manual events: {e}")

    # 2. Grant Events: Milestones
    try:
        if user.role == 'RSU':
            milestones = models.Milestone.query.all()
        else:
            milestones = models.Milestone.query.filter(models.Milestone.grant_id.in_(my_grant_ids)).all()

        for m in milestones:
            events.append({
                'id': f'milestone-{m.id}',
                'title': f'Milestone: {m.title}',
                'description': m.description,
                'event_date': datetime.combine(m.due_date, datetime.min.time()).isoformat(),
                'event_type': 'GRANT',
                'grant_id': m.grant_id,
                'grant_title': m.grant.title if m.grant else 'Unknown'
            })
    except Exception as e:
        print(f"Error fetching milestone events: {e}")

    return jsonify(events)

@calendar_bp.route('/events', methods=['POST'])
def create_event():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    try:
        new_event = models.CalendarEvent(
            title=data['title'],
            description=data.get('description'),
            event_date=datetime.fromisoformat(data['event_date'].replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None,
            event_type=data['event_type'],
            grant_id=data.get('grant_id'),
            user_id=user_id,
            target_role=data.get('target_role')
        )
        
        models.db.session.add(new_event)
        models.db.session.commit()
        
        return jsonify(new_event.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calendar_bp.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    event = models.CalendarEvent.query.get_or_404(event_id)
    if event.user_id != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    
    models.db.session.delete(event)
    models.db.session.commit()
    
    return jsonify({'message': 'Event deleted successfully'})
