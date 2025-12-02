from repositories.budget_repository import BudgetRepository
from repositories.grant_repository import GrantRepository


class BudgetService:
    """Business rules for grant budgets and category burn rates."""

    def __init__(self, budget_repo: BudgetRepository = BudgetRepository, grant_repo: GrantRepository = GrantRepository):
        self.budget_repo = budget_repo
        self.grant_repo = grant_repo

    def summarize_grant_budget(self, grant_id: int) -> dict:
        grant = self.grant_repo.find_by_id(grant_id)
        categories = self.budget_repo.list_for_grant(grant_id)
        allocated = sum(cat.allocated for cat in categories)
        spent = sum(cat.spent for cat in categories)
        return {
            'grant': grant.to_dict() if grant else None,
            'allocated': allocated,
            'spent': spent,
            'categories': [cat.to_dict() for cat in categories]
        }

    def update_category_spent(self, category_id: int, amount: float) -> dict:
        category = self.budget_repo.find_by_id(category_id)
        if not category:
            raise ValueError('Budget category not found')
        category.spent = amount
        updated = self.budget_repo.save(category)
        return updated.to_dict()
