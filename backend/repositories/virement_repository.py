from typing import Optional, List
from models import db, BudgetVirement

class VirementRepository:
    """CRUD helpers for budget virements."""

    @staticmethod
    def find_by_id(virement_id: int) -> Optional[BudgetVirement]:
        return BudgetVirement.query.get(virement_id)

    @staticmethod
    def list_for_grant(grant_id: int) -> List[BudgetVirement]:
        return BudgetVirement.query.filter_by(grant_id=grant_id).all()

    @staticmethod
    def save(virement: BudgetVirement) -> BudgetVirement:
        db.session.add(virement)
        db.session.commit()
        return virement

    @staticmethod
    def delete(virement: BudgetVirement) -> None:
        db.session.delete(virement)
        db.session.commit()
