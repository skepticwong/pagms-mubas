from models import db, Notification, User
from datetime import datetime

class NotificationService:
    @staticmethod
    def notify_user(user_id, n_type, message, data=None):
        """
        Generic user notification (DB-based).
        """
        notification = Notification(
            user_id=user_id,
            type=n_type,
            message=message,
            data=data,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def notify_role(role, n_type, message, data=None):
        """
        Notify all users of a specific role (e.g., 'FINANCE', 'RSU').
        """
        users = User.query.filter_by(role=role).all()
        notifications = []
        for user in users:
            notifications.append(
                Notification(
                    user_id=user.id,
                    type=n_type,
                    message=message,
                    data=data,
                    created_at=datetime.utcnow()
                )
            )
        db.session.add_all(notifications)
        db.session.commit()
        return notifications

    @staticmethod
    def notify_rule_event(user_id, event_type, details):
        """
        Compatibility method for the Rules Engine.
        """
        message = f"Rule Event: {event_type} - {details.get('notes', '')}"
        return NotificationService.notify_user(user_id, event_type, message, details)
