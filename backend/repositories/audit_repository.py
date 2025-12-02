from typing import Optional

from models import db, AuditLog


class AuditRepository:
    """Persistence helper for audit log entries."""

    @staticmethod
    def log(audit: AuditLog) -> AuditLog:
        db.session.add(audit)
        db.session.commit()
        return audit

    @staticmethod
    def find_by_id(audit_id: int) -> Optional[AuditLog]:
        return AuditLog.query.get(audit_id)

    @staticmethod
    def list_recent(limit: int = 100) -> list[AuditLog]:
        return AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
