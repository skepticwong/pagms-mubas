from flask import Blueprint, request, jsonify, session
import models
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
    manual_events = models.CalendarEvent.query.filter(
        models.db.or_(
            models.CalendarEvent.event_type == 'BROADCAST',
            models.CalendarEvent.user_id == user_id,
            (models.CalendarEvent.grant_id != None) & (models.CalendarEvent.grant_id.in_([g.id for g in user.grants_as_pi] + [gt.grant_id for gt in user.grant_roles]))
        )
    ).all()
    events.extend([e.to_dict() for e in manual_events])

    # 2. System Events: REC Meetings
    if user.role == 'RSU':
        rec_meetings = models.Grant.query.filter(models.Grant.rec_meeting_date != None).all()
    else:
        # Only for their grants
        my_grant_ids = [g.id for g in user.grants_as_pi] + [gt.grant_id for gt in user.grant_roles]
        rec_meetings = models.Grant.query.filter(models.Grant.id.in_(my_grant_ids), models.Grant.rec_meeting_date != None).all()
    
    for grant in rec_meetings:
        events.append({
            'id': f'rec-{grant.id}',
            'title': f'REC Meeting: {grant.title}',
            'description': f'REC meeting for {grant.grant_code}',
            'event_date': datetime.combine(grant.rec_meeting_date, datetime.min.time()).isoformat(),
            'event_type': 'SYSTEM',
            'grant_id': grant.id,
            'grant_title': grant.title
        })

    # 3. System Events: Ethics Expiries
    if user.role == 'RSU':
        ethics_expiries = models.Grant.query.filter(models.Grant.ethics_expiry_date != None).all()
    else:
        my_grant_ids = [g.id for g in user.grants_as_pi] + [gt.grant_id for gt in user.grant_roles]
        ethics_expiries = models.Grant.query.filter(models.Grant.id.in_(my_grant_ids), models.Grant.ethics_expiry_date != None).all()

    for grant in ethics_expiries:
        events.append({
            'id': f'ethics-{grant.id}',
            'title': f'Ethics Expiry: {grant.title}',
            'description': f'Ethics approval expires for {grant.grant_code}',
            'event_date': datetime.combine(grant.ethics_expiry_date, datetime.min.time()).isoformat(),
            'event_type': 'SYSTEM',
            'grant_id': grant.id,
            'grant_title': grant.title
        })

    # 4. Grant Events: Milestones
    if user.role == 'RSU':
        milestones = models.Milestone.query.all()
    else:
        my_grant_ids = [g.id for g in user.grants_as_pi] + [gt.grant_id for gt in user.grant_roles]
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
