from datetime import datetime
from models import db, AuditTrail, User

class AuditService:
    @staticmethod
    def log_action(user_id, action, entity_type, entity_id, details=None, is_override=False, ip_address=None):
        """
        Global Master Log. Standardized for forensic-ready auditing.
        Append-only strategy.
        """
        # 1. Standardize Entry
        audit = AuditTrail(
            user_id=user_id,
            action=action.upper(),
            entity_type=entity_type.upper(),
            entity_id=entity_id,
            details=details,
            is_override=is_override,
            timestamp=datetime.utcnow(),
            ip_address=ip_address
        )
        
        # 2. Add to Session
        db.session.add(audit)
        
        # 3. Commit immediately for high-security actions
        try:
            db.session.commit()
            return audit
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_audit_history(entity_type=None, entity_id=None, limit=100):
        """Fetches history for a specific entity."""
        query = AuditTrail.query
        if entity_type:
            query = query.filter_by(entity_type=entity_type.upper())
        if entity_id:
            query = query.filter_by(entity_id=entity_id)
        
        return query.order_by(AuditTrail.timestamp.desc()).limit(limit).all()

    @staticmethod
    def log_security_event(user_id, event_type, details=None, ip_address=None):
        """Specific logs for logins, unauthorized access, and status changes."""
        return AuditService.log_action(
            user_id=user_id,
            action=event_type,
            entity_type='SECURITY',
            entity_id=user_id,
            details=details,
            ip_address=ip_address
        )
