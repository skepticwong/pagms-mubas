from typing import Optional

from models import db, ExchangeRate


class ExchangeRateRepository:
    """CRUD helpers for FX reference rates."""

    @staticmethod
    def find_by_currency(currency: str) -> Optional[ExchangeRate]:
        return ExchangeRate.query.filter_by(currency=currency).first()

    @staticmethod
    def list_all() -> list[ExchangeRate]:
        return ExchangeRate.query.order_by(ExchangeRate.currency.asc()).all()

    @staticmethod
    def save(rate: ExchangeRate) -> ExchangeRate:
        db.session.add(rate)
        db.session.commit()
        return rate
