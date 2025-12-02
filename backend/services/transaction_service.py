from repositories.transaction_repository import TransactionRepository
from repositories.expense_repository import ExpenseRepository
from repositories.audit_repository import AuditRepository


class TransactionService:
    """Handles approved / paid transaction audit trail."""

    def __init__(
        self,
        transaction_repo: TransactionRepository = TransactionRepository,
        expense_repo: ExpenseRepository = ExpenseRepository,
        audit_repo: AuditRepository = AuditRepository,
    ):
        self.transaction_repo = transaction_repo
        self.expense_repo = expense_repo
        self.audit_repo = audit_repo

    def list_recent(self, limit: int = 50) -> list[dict]:
        transactions = self.transaction_repo.list_recent(limit)
        return [trx.to_dict() for trx in transactions]

    def record_payment(self, expense_id: int, payment_reference: str, approver_id: int) -> dict:
        expense = self.expense_repo.find_by_id(expense_id)
        if not expense:
            raise ValueError('Expense not found')
        from models import Transaction

        transaction = Transaction(
            expense_id=expense.id,
            grant_id=expense.grant_id,
            vendor='TBD',
            amount=expense.amount,
            currency=expense.currency,
            payment_reference=payment_reference,
            approved_by=approver_id,
        )
        saved = self.transaction_repo.save(transaction)
        self._log_action('transaction', saved.id, approver_id, 'recorded payment')
        return saved.to_dict()

    def _log_action(self, resource_type: str, resource_id: int, user_id: int, action: str):
        from models import AuditLog

        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        self.audit_repo.log(audit)
