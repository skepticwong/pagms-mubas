from models import db, Grant, RuleEvaluation, ExpenseClaim, BudgetCategory
from datetime import datetime, timedelta

class ComplianceService:
    @staticmethod
    def calculate_health_score(grant_id):
        """
        Calculates a compliance health status (Green, Yellow, Red).
        Logic:
        - RED: Any recent BLOCK evaluation or category > 100% spent.
        - YELLOW: Any recent PRIOR_APPROVAL or category > 90% spent.
        - GREEN: Otherwise.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            return 'GRAY'

        # 1. Check for recent BLOCKS
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_blocks = RuleEvaluation.query.filter(
            RuleEvaluation.grant_id == grant_id,
            RuleEvaluation.final_outcome == 'BLOCK',
            RuleEvaluation.evaluated_at >= seven_days_ago
        ).count()
        
        if recent_blocks > 0:
            return 'RED'

        # 2. Check for budget overruns
        categories = BudgetCategory.query.filter_by(grant_id=grant_id).all()
        max_burn = 0
        if categories:
            max_burn = max([(c.spent / c.allocated * 100) if c.allocated > 0 else 0 for c in categories])
        
        if max_burn > 100:
            return 'RED'
        if max_burn > 90:
            return 'YELLOW'

        # 3. Check for pending prior approvals
        pending_approvals = RuleEvaluation.query.filter(
            RuleEvaluation.grant_id == grant_id,
            RuleEvaluation.final_outcome == 'PRIOR_APPROVAL',
            RuleEvaluation.resolved_at == None
        ).count()

        if pending_approvals > 0:
            return 'YELLOW'

        return 'GREEN'

    @staticmethod
    def get_compliance_summary(grant_id):
        """Returns a summary of compliance status for reports."""
        score = ComplianceService.calculate_health_score(grant_id)
        
        # Get count of triggered rules in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        evaluations = RuleEvaluation.query.filter(
            RuleEvaluation.grant_id == grant_id,
            RuleEvaluation.evaluated_at >= thirty_days_ago
        ).all()
        
        return {
            'status': score,
            'total_checks': len(evaluations),
            'blocks': len([e for e in evaluations if e.final_outcome == 'BLOCK']),
            'prior_approvals': len([e for e in evaluations if e.final_outcome == 'PRIOR_APPROVAL']),
            'warnings': len([e for e in evaluations if e.final_outcome == 'WARN'])
        }
