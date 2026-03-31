from typing import List, Optional
from models import db, BudgetVirement, BudgetCategory
from repositories.virement_repository import VirementRepository
from repositories.budget_repository import BudgetRepository
from services.workflow_service import WorkflowService
from services.rule_service import RuleService
from services.audit_service import AuditService
from services.health_score_service import HealthScoreService
from datetime import datetime

class VirementService:
    """Business logic for budget reallocations (virements) with rules-driven encumbrance and workflow."""

    def __init__(
        self, 
        virement_repo: VirementRepository = VirementRepository,
        budget_repo: BudgetRepository = BudgetRepository,
        workflow_service: WorkflowService = WorkflowService()
    ):
        self.virement_repo = virement_repo
        self.budget_repo = budget_repo
        self.workflow_service = workflow_service

    def create_virement_request(
        self, 
        grant_id: int, 
        from_category_id: int, 
        to_category_id: int, 
        amount: float, 
        justification: str, 
        user_id: int
    ) -> BudgetVirement:
        """
        Creates a new virement request and encumbers the funds in the source category.
        """
        if amount <= 0:
            raise ValueError("Virement amount must be positive.")

        from_cat = self.budget_repo.find_by_id(from_category_id)
        to_cat = self.budget_repo.find_by_id(to_category_id)

        if not from_cat or not to_cat:
            raise ValueError("One or both budget categories not found.")

        if from_cat.grant_id != grant_id or to_cat.grant_id != grant_id:
            raise ValueError("Categories must belong to the same grant.")

        # Availability Check: allocated - spent - encumbered
        available = from_cat.allocated - from_cat.spent - from_cat.encumbered
        if available < amount:
            raise ValueError(f"Insufficient funds in source category. Available: {available}, Requested: {amount}")

        # --- Rule Engine Integration ---
        # Construct context for rules
        # Percent of total grant budget being reallocated
        grant = from_cat.grant # Loaded through relationship
        percent_of_total = (amount / grant.total_budget) if grant.total_budget > 0 else 0
        
        rule_context = {
            'amount': amount,
            'percent_of_total': percent_of_total,
            'source_category': from_cat.name.lower(),
            'dest_category': to_cat.name.lower(),
            'category': 'virement' # Action broad category
        }
        
        evaluation = RuleService.evaluate_action('BUDGET_REALLOCATION', rule_context, grant_id, user_id=user_id)
        outcome = evaluation.get('outcome', 'PASS')
        
        if outcome == 'BLOCK':
            reasons = [r.get('guidance_text', 'Rule violation') for r in evaluation.get('triggered_rules', [])]
            raise ValueError(f"Virement Blocked: {', '.join(reasons)}")

        # 1. Create Virement Record
        virement = BudgetVirement(
            grant_id=grant_id,
            from_category_id=from_category_id,
            to_category_id=to_category_id,
            amount=amount,
            justification=justification,
            created_by_id=user_id,
            status='pending'
        )
        saved_virement = self.virement_repo.save(virement)

        # 2. Encumber funds (immediately)
        from_cat.encumbered += amount
        self.budget_repo.save(from_cat)

        # 3. Handle Auto-Approval vs Workflow
        if outcome in ['PASS', 'WARN']:
            # Auto-approve!
            return self.approve_virement(saved_virement.id, user_id)
        
        # PRIOR_APPROVAL required
        steps_config = [
            {'role': 'FINANCE', 'order': 1},
            {'role': 'RSU', 'order': 2}
        ]
        workflow = self.workflow_service.init_workflow('VIREMENT', saved_virement.id, steps_config, grant_id=grant_id)
        
        saved_virement.workflow_id = workflow.id
        
        # 4. Forensic Audit & Health Update
        AuditService.log_action(
            user_id=user_id,
            action='VIREMENT_REQUESTED',
            entity_type='BUDGET',
            entity_id=saved_virement.id,
            details={
                'amount': amount,
                'from': from_cat.name,
                'to': to_cat.name,
                'outcome': outcome
            }
        )
        
        if outcome in ['BLOCK', 'PRIOR_APPROVAL', 'WARN']:
            HealthScoreService.calculate_score(grant_id)

        return self.virement_repo.save(saved_virement)

    def approve_virement(self, virement_id: int, user_id: int) -> BudgetVirement:
        """
        Approves a virement, moves the funds, and releases the encumbrance.
        """
        virement = self.virement_repo.find_by_id(virement_id)
        if not virement or virement.status != 'pending':
            raise ValueError("Invalid virement request or virement not pending.")

        from_cat = self.budget_repo.find_by_id(virement.from_category_id)
        to_cat = self.budget_repo.find_by_id(virement.to_category_id)

        # Move allocated funds
        from_cat.allocated -= virement.amount
        to_cat.allocated += virement.amount

        # Release encumbrance
        from_cat.encumbered -= virement.amount

        # Update virement status
        virement.status = 'approved'
        virement.resolved_at = datetime.utcnow()

        self.budget_repo.save(from_cat)
        self.budget_repo.save(to_cat)
        return self.virement_repo.save(virement)

    def reject_virement(self, virement_id: int, user_id: int, comment: Optional[str] = None) -> BudgetVirement:
        """
        Rejects a virement and releases the encumbrance.
        """
        virement = self.virement_repo.find_by_id(virement_id)
        if not virement or virement.status != 'pending':
            raise ValueError("Invalid virement request or virement not pending.")

        from_cat = self.budget_repo.find_by_id(virement.from_category_id)

        # Release encumbrance
        from_cat.encumbered -= virement.amount

        # Update virement status
        virement.status = 'rejected'
        virement.resolved_at = datetime.utcnow()
        if comment:
            virement.justification += f"\n\nRejection Comment: {comment}"

        self.budget_repo.save(from_cat)
        return self.virement_repo.save(virement)

    def list_virements_for_grant(self, grant_id: int) -> List[BudgetVirement]:
        return self.virement_repo.list_for_grant(grant_id)
