from typing import Optional

from models import db, Grant


class GrantRepository:
    """Data access helper for grant-level operations."""

    @staticmethod
    def find_by_id(grant_id: int) -> Optional[Grant]:
        return Grant.query.get(grant_id)

    @staticmethod
    def find_by_code(grant_code: str) -> Optional[Grant]:
        return Grant.query.filter_by(grant_code=grant_code).first()

    @staticmethod
    def list_active() -> list[Grant]:
        return Grant.query.filter_by(status='active').all()

    @staticmethod
    def list_for_pi(pi_id: int) -> list[Grant]:
        return Grant.query.filter_by(pi_id=pi_id).order_by(Grant.created_at.desc()).all()

    @staticmethod
    def save(grant: Grant, commit: bool = True) -> Grant:
        db.session.add(grant)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return grant

    @staticmethod
    def search(keyword: str) -> list[Grant]:
        search_term = f"%{keyword}%"
        return Grant.query.filter(Grant.title.ilike(search_term) | Grant.grant_code.ilike(search_term)).all()
