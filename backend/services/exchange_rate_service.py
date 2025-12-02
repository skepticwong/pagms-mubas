from datetime import datetime

from repositories.exchange_rate_repository import ExchangeRateRepository
from repositories.audit_repository import AuditRepository


class ExchangeRateService:
    """Controls fetching and updating FX reference rates."""

    def __init__(
        self,
        rate_repo: ExchangeRateRepository = ExchangeRateRepository,
        audit_repo: AuditRepository = AuditRepository,
    ):
        self.rate_repo = rate_repo
        self.audit_repo = audit_repo

    def list_rates(self) -> list[dict]:
        return [rate.to_dict() for rate in self.rate_repo.list_all()]

    def update_rate(self, currency: str, buying: float, selling: float, spread: float, user_id: int) -> dict:
        rate = self.rate_repo.find_by_currency(currency)
        if not rate:
            from models import ExchangeRate

            rate = ExchangeRate(currency=currency)
        rate.buying_rate = buying
        rate.selling_rate = selling
        rate.buffer_spread = spread
        rate.last_updated = datetime.utcnow()
        saved = self.rate_repo.save(rate)
        self._log_action('exchange_rate', saved.id, user_id, f'updated {currency} rate')
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
