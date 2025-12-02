from datetime import datetime

from models import ExpenseClaim
from repositories.expense_repository import ExpenseRepository
from repositories.audit_repository import AuditRepository


class ExpenseService:
    """Handles finance pending expenses lifecycle."""

    def __init__(
        self,
        expense_repo: ExpenseRepository = ExpenseRepository,
        audit_repo: AuditRepository = AuditRepository,
    ):
        self.expense_repo = expense_repo
        self.audit_repo = audit_repo

    def list_pending(self) -> list[dict]:
        return [expense.to_dict() for expense in self.expense_repo.list_pending()]

    def approve(self, expense_id: int, approver_id: int) -> dict:
        expense = self.expense_repo.find_by_id(expense_id)
        if not expense:
            raise ValueError('Expense not found')
        expense.status = 'approved'
        expense.approved_at = datetime.utcnow()
        updated = self.expense_repo.save(expense)
        self._log_action('expense', expense_id, approver_id, 'approved expense')
        return updated.to_dict()

    def reject(self, expense_id: int, approver_id: int, reason: str) -> dict:
        expense = self.expense_repo.find_by_id(expense_id)
        if not expense:
            raise ValueError('Expense not found')
        expense.status = 'rejected'
        updated = self.expense_repo.save(expense)
        details = f"reason={reason}"
        self._log_action('expense', expense_id, approver_id, 'rejected expense', details)
        return updated.to_dict()

    def _log_action(self, resource_type: str, resource_id: int, user_id: int, action: str, details: str = ''):
        from models import AuditLog

        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
        self.audit_repo.log(audit)
