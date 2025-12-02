from typing import Optional

from models import db, BudgetCategory


class BudgetRepository:
    """CRUD helpers for budget categories and grant-level budget views."""

    @staticmethod
    def find_by_id(category_id: int) -> Optional[BudgetCategory]:
        return BudgetCategory.query.get(category_id)

    @staticmethod
    def list_for_grant(grant_id: int) -> list[BudgetCategory]:
        return BudgetCategory.query.filter_by(grant_id=grant_id).all()

    @staticmethod
    def save(category: BudgetCategory) -> BudgetCategory:
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def delete(category: BudgetCategory) -> None:
        db.session.delete(category)
        db.session.commit()
