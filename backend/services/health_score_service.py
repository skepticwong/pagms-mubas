from datetime import datetime, timedelta
from models import db, Grant, ComplianceHealthScore, RuleEvaluation, AuditTrail

class HealthScoreService:
    @staticmethod
    def calculate_score(grant_id, commit=True):
        """
        The Risk Heatmap Logic. 
        Formula: 100 - (Penalty_Points)
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            return None

        health = ComplianceHealthScore.query.filter_by(grant_id=grant_id).first()
        if not health:
            health = ComplianceHealthScore(grant_id=grant_id, score=100, risk_level='LOW')
            db.session.add(health)

        penalty_points = 0
        financial_risk = 0
        operational_risk = 0
        reporting_risk = 0

        # 1. Critical Block Occurred (-20)
        blocks = RuleEvaluation.query.filter_by(grant_id=grant_id, outcome='BLOCK').count()
        if blocks > 0:
            penalty_points += 20
            financial_risk += 10

        # 2. Prior Approval Pending > 5 days (-5)
        # Assuming we track pending approvals elsewhere, we can check RuleEvaluation for PRIOR_APPROVAL
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        pending_approvals = RuleEvaluation.query.filter(
            RuleEvaluation.grant_id == grant_id,
            RuleEvaluation.outcome == 'PRIOR_APPROVAL',
            RuleEvaluation.timestamp < five_days_ago
        ).count()
        penalty_points += pending_approvals * 5
        operational_risk += pending_approvals * 2

        # 3. Ethics Expired (-50 - Instant RED)
        # Check Grant's ethical approval date if it exists (assuming we might add it or check deliverables)
        # For now, we'll check if a rule evaluation specifically for ETHICS has a BLOCK/BLOCK outcome
        ethics_blocks = RuleEvaluation.query.filter_by(grant_id=grant_id, action_type='ETHICS', outcome='BLOCK').count()
        if ethics_blocks > 0:
            penalty_points += 50
            operational_risk += 30

        # 4. Report Overdue (-15)
        # Assuming we can check Milestones for overdue reports
        from models import Milestone
        overdue_reports = Milestone.query.filter(
            Milestone.grant_id == grant_id,
            Milestone.status != 'COMPLETED',
            Milestone.due_date < datetime.utcnow().date(),
            Milestone.reporting_period.isnot(None)
        ).count()
        penalty_points += overdue_reports * 15
        reporting_risk += overdue_reports * 10

        # 5. Asset Overdue (-5)
        # Placeholder for asset check
        from models import Asset
        overdue_assets = Asset.query.filter(
            Asset.grant_id == grant_id,
            Asset.status == 'OVERDUE'
        ).count()
        penalty_points += overdue_assets * 5
        operational_risk += overdue_assets * 2

        # Calculate Final Score
        health.score = max(0, 100 - penalty_points)
        health.financial_risk = financial_risk
        health.operational_risk = operational_risk
        health.reporting_risk = reporting_risk
        health.last_calculated = datetime.utcnow()

        # Resolve Risk Level
        # 90-100: LOW, 70-89: MEDIUM, 40-69: HIGH, 0-39: CRITICAL
        if health.score >= 90:
            health.risk_level = 'LOW'
        elif health.score >= 70:
            health.risk_level = 'MEDIUM'
        elif health.score >= 40:
            health.risk_level = 'HIGH'
        else:
            health.risk_level = 'CRITICAL'

        if commit:
            db.session.commit()

        return health.to_dict()
