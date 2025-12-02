from typing import Optional

from models import db, ExpenseClaim


class ExpenseRepository:
    """Persistence operations for expense claims."""

    @staticmethod
    def find_by_id(expense_id: int) -> Optional[ExpenseClaim]:
        return ExpenseClaim.query.get(expense_id)

    @staticmethod
    def list_pending() -> list[ExpenseClaim]:
        return ExpenseClaim.query.filter_by(status='pending').all()

    @staticmethod
    def list_by_grant(grant_id: int) -> list[ExpenseClaim]:
        return ExpenseClaim.query.filter_by(grant_id=grant_id).all()

    @staticmethod
    def save(expense: ExpenseClaim) -> ExpenseClaim:
        db.session.add(expense)
        db.session.commit()
        return expense
