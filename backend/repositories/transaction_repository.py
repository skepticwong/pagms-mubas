from typing import Optional

from models import db, Transaction


class TransactionRepository:
    """Handles approved / paid transaction persistence."""

    @staticmethod
    def find_by_id(transaction_id: int) -> Optional[Transaction]:
        return Transaction.query.get(transaction_id)

    @staticmethod
    def list_recent(limit: int = 50) -> list[Transaction]:
        return Transaction.query.order_by(Transaction.paid_on.desc()).limit(limit).all()

    @staticmethod
    def save(transaction: Transaction) -> Transaction:
        db.session.add(transaction)
        db.session.commit()
        return transaction
