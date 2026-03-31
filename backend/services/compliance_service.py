from models import db, Grant, RuleEvaluation, ExpenseClaim, BudgetCategory, ComplianceMonitoring
from datetime import datetime, timedelta

class ComplianceService:
    @staticmethod
    def calculate_health_score(grant_id, commit=True):
        """
        Calculates a compliance health status using the expert ComplianceMonitoring model.
        """
        # Trigger the expert scoring logic
        rec = ComplianceMonitoring.calculate_compliance_score(grant_id, commit=commit)
        
        # Map risk levels to colors
        risk_map = {
            'low': 'GREEN',
            'medium': 'YELLOW',
            'high': 'RED',
            'critical': 'RED'
        }
        return risk_map.get(rec.risk_level, 'GRAY')

    @staticmethod
    def get_compliance_summary(grant_id, commit=True):
        """Returns a summary of compliance status for reports using the expert record."""
        rec = ComplianceMonitoring.calculate_compliance_score(grant_id, commit=commit)
        
        # Get count of triggered rules in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        evaluations = RuleEvaluation.query.filter(
            RuleEvaluation.grant_id == grant_id,
            RuleEvaluation.evaluated_at >= thirty_days_ago
        ).all()
        
        return {
            'status': ComplianceService.calculate_health_score(grant_id, commit=False),
            'overall_score': rec.overall_score,
            'risk_level': rec.risk_level,
            'total_checks': len(evaluations),
            'blocks': len([e for e in evaluations if e.final_outcome == 'BLOCK']),
            'prior_approvals': len([e for e in evaluations if e.final_outcome == 'PRIOR_APPROVAL']),
            'warnings': len([e for e in evaluations if e.final_outcome == 'WARN']),
            'updated_at': rec.updated_at.isoformat() if rec.updated_at else None
        }
