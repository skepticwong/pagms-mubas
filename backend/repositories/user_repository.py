from typing import Optional

from models import db, User


class UserRepository:
    """Data access helper for User records."""

    @staticmethod
    def find_by_id(user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    @staticmethod
    def find_by_email(email: str) -> Optional[User]:
        return User.query.filter_by(email=email).first()

    @staticmethod
    def save(user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def list_all() -> list[User]:
        return User.query.order_by(User.created_at.desc()).all()
