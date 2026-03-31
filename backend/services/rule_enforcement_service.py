"""
Rule Enforcement Service - Provides real-time monitoring and enforcement of rules
across the entire system for maximum control and compliance.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import db, Rule, FunderProfile, RuleEvaluation, Grant, ExpenseClaim, GrantTeam, BudgetCategory
from services.rule_service import RuleService
from services.notification_service import NotificationService

class RuleEnforcementService:
    """Enhanced rule enforcement with real-time monitoring and system-wide control"""
    
    @staticmethod
    def monitor_system_compliance():
        """
        Background task that monitors all active grants for compliance violations
        Returns summary of compliance issues found
        """
        compliance_issues = []
        active_grants = Grant.query.filter(Grant.status.in_(['active', 'pending'])).all()
        
        for grant in active_grants:
            issues = RuleEnforcementService._check_grant_compliance(grant)
            if issues:
                compliance_issues.extend(issues)
                
        return {
            'total_issues': len(compliance_issues),
            'issues': compliance_issues,
            'checked_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _check_grant_compliance(grant) -> List[Dict]:
        """Check a specific grant for all compliance issues"""
        issues = []
        
        # Check budget compliance
        budget_issues = RuleEnforcementService._check_budget_compliance(grant)
        issues.extend(budget_issues)
        
        # Check personnel compliance
        personnel_issues = RuleEnforcementService._check_personnel_compliance(grant)
        issues.extend(personnel_issues)
        
        # Check expense compliance
        expense_issues = RuleEnforcementService._check_expense_compliance(grant)
        issues.extend(expense_issues)
        
        # Check temporal compliance (deadlines, reporting)
        temporal_issues = RuleEnforcementService._check_temporal_compliance(grant)
        issues.extend(temporal_issues)
        
        return issues
    
    @staticmethod
    def _check_budget_compliance(grant) -> List[Dict]:
        """Check budget-related compliance"""
        issues = []
        
        # Check overspending in categories
        for category in grant.categories:
            spent = sum([expense.amount for expense in category.expenses 
                        if expense.status == 'approved'])
            if spent > category.budget_allocation:
                issues.append({
                    'type': 'BUDGET_OVERSPEND',
                    'severity': 'HIGH',
                    'grant_id': grant.id,
                    'category': category.name,
                    'budget': category.budget_allocation,
                    'spent': spent,
                    'overspend': spent - category.budget_allocation,
                    'message': f"Overspending by {spent - category.budget_allocation} in {category.name}"
                })
        
        # Check total budget utilization
        total_spent = sum([c.spent for c in grant.categories])
        if total_spent > grant.total_budget:
            issues.append({
                'type': 'TOTAL_BUDGET_EXCEEDED',
                'severity': 'CRITICAL',
                'grant_id': grant.id,
                'total_budget': grant.total_budget,
                'total_spent': total_spent,
                'overspend': total_spent - grant.total_budget,
                'message': f"Total grant budget exceeded by {total_spent - grant.total_budget}"
            })
        
        return issues
    
    @staticmethod
    def _check_personnel_compliance(grant) -> List[Dict]:
        """Check personnel-related compliance"""
        issues = []
        
        # Check team size limits
        team_size = len([m for m in grant.team_members if m.status == 'active'])
        context = {'team_size': team_size, 'category': 'personnel'}
        
        result = RuleService.evaluate_action('PERSONNEL_COMPLIANCE', context, grant.id, commit=False)
        if result['outcome'] != 'PASS':
            issues.append({
                'type': 'PERSONNEL_COMPLIANCE',
                'severity': 'MEDIUM',
                'grant_id': grant.id,
                'team_size': team_size,
                'message': f"Personnel compliance issue: {result['triggered_rules'][0]['guidance_text']}"
            })
        
        return issues
    
    @staticmethod
    def _check_expense_compliance(grant) -> List[Dict]:
        """Check expense-related compliance"""
        issues = []
        
        # Check for unapproved high-value expenses
        high_value_expenses = ExpenseClaim.query.filter(
            ExpenseClaim.grant_id == grant.id,
            ExpenseClaim.amount > 500000,  # MWK 500,000 threshold
            ExpenseClaim.status.in_(['pending', 'draft'])
        ).all()
        
        for expense in high_value_expenses:
            issues.append({
                'type': 'HIGH_VALUE_EXPENSE_PENDING',
                'severity': 'HIGH',
                'grant_id': grant.id,
                'expense_id': expense.id,
                'amount': expense.amount,
                'message': f"High-value expense ({expense.amount}) awaiting approval"
            })
        
        return issues
    
    @staticmethod
    def _check_temporal_compliance(grant) -> List[Dict]:
        """Check time-based compliance"""
        issues = []
        today = datetime.utcnow().date()
        
        # Check grant expiration
        if grant.end_date and today > grant.end_date:
            issues.append({
                'type': 'GRANT_EXPIRED',
                'severity': 'CRITICAL',
                'grant_id': grant.id,
                'end_date': grant.end_date.isoformat(),
                'days_expired': (today - grant.end_date).days,
                'message': f"Grant expired {(today - grant.end_date).days} days ago"
            })
        elif grant.end_date and (grant.end_date - today).days <= 30:
            issues.append({
                'type': 'GRANT_EXPIRING_SOON',
                'severity': 'HIGH',
                'grant_id': grant.id,
                'end_date': grant.end_date.isoformat(),
                'days_remaining': (grant.end_date - today).days,
                'message': f"Grant expires in {(grant.end_date - today).days} days"
            })
        
        # Check reporting deadlines
        if grant.financial_reporting_frequency:
            next_report = RuleEnforcementService._calculate_next_reporting_date(
                grant, grant.financial_reporting_frequency
            )
            if next_report and (next_report - today).days <= 7:
                issues.append({
                    'type': 'REPORTING_DEADLINE_APPROACHING',
                    'severity': 'MEDIUM',
                    'grant_id': grant.id,
                    'next_report_date': next_report.isoformat(),
                    'days_remaining': (next_report - today).days,
                    'message': f"Financial report due in {(next_report - today).days} days"
                })
        
        return issues
    
    @staticmethod
    def _calculate_next_reporting_date(grant, frequency) -> datetime:
        """Calculate next reporting date based on frequency"""
        if not frequency or not grant.start_date:
            return None
            
        today = datetime.utcnow().date()
        start_date = grant.start_date
        
        if frequency == 'monthly':
            # Next month start
            next_month = today.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=1)
        elif frequency == 'quarterly':
            # Next quarter start
            month = ((today.month - 1) // 3) * 3 + 1
            if month <= today.month:
                month += 12
            return today.replace(month=month, day=1)
        elif frequency == 'annually':
            # Next anniversary
            next_anniversary = today.replace(month=start_date.month, day=start_date.day)
            if next_anniversary <= today:
                next_anniversary = next_anniversary.replace(year=today.year + 1)
            return next_anniversary
        
        return None
    
    @staticmethod
    def enforce_rule_violations(violations: List[Dict]):
        """
        Take automatic enforcement actions based on rule violations
        This gives the rules engine "teeth" to enforce compliance
        """
        enforcement_actions = []
        
        for violation in violations:
            action = RuleEnforcementService._determine_enforcement_action(violation)
            if action:
                enforcement_actions.append(action)
                RuleEnforcementService._execute_enforcement_action(action)
        
        return enforcement_actions
    
    @staticmethod
    def _determine_enforcement_action(violation: Dict) -> Dict:
        """Determine appropriate enforcement action for a violation"""
        severity = violation.get('severity', 'LOW')
        violation_type = violation.get('type')
        
        if severity == 'CRITICAL':
            return {
                'type': 'IMMEDIATE_FREEZE',
                'violation': violation,
                'action': 'freeze_grant_activities',
                'reason': f"Critical violation: {violation['message']}"
            }
        elif severity == 'HIGH':
            if violation_type in ['BUDGET_OVERSPEND', 'HIGH_VALUE_EXPENSE_PENDING']:
                return {
                    'type': 'REQUIRE_APPROVAL',
                    'violation': violation,
                    'action': 'escalate_to_rsu',
                    'reason': f"High priority violation: {violation['message']}"
                }
            else:
                return {
                    'type': 'NOTIFY_PI',
                    'violation': violation,
                    'action': 'send_immediate_notification',
                    'reason': f"High priority issue: {violation['message']}"
                }
        elif severity == 'MEDIUM':
            return {
                'type': 'SCHEDULE_REVIEW',
                'violation': violation,
                'action': 'schedule_compliance_review',
                'reason': f"Medium priority issue: {violation['message']}"
            }
        
        return None
    
    @staticmethod
    def _execute_enforcement_action(action: Dict):
        """Execute the enforcement action"""
        action_type = action['type']
        violation = action['violation']
        grant_id = violation['grant_id']
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return
        
        if action_type == 'IMMEDIATE_FREEZE':
            # Freeze grant activities
            grant.status = 'compliance_hold'
            db.session.commit()
            
            # Notify all stakeholders
            NotificationService.notify_rule_event(
                grant.pi_id, 
                'GRANT_FROZEN', 
                {
                    'grant_id': grant.id,
                    'reason': action['reason'],
                    'action_required': 'Contact RSU immediately'
                }
            )
            
        elif action_type == 'REQUIRE_APPROVAL':
            # Create escalation ticket
            NotificationService.notify_rule_event(
                grant.pi_id, 
                'COMPLIANCE_ESCALATION', 
                {
                    'grant_id': grant.id,
                    'issue': violation['message'],
                    'action_required': 'Immediate RSU approval required'
                }
            )
            
        elif action_type == 'NOTIFY_PI':
            # Send immediate notification
            NotificationService.notify_rule_event(
                grant.pi_id, 
                'COMPLIANCE_WARNING', 
                {
                    'grant_id': grant.id,
                    'warning': violation['message'],
                    'action_required': 'Review and address compliance issue'
                }
            )
    
    @staticmethod
    def get_compliance_dashboard():
        """Get comprehensive compliance overview for dashboard"""
        active_grants = Grant.query.filter(Grant.status.in_(['active', 'pending'])).count()
        
        # Get recent violations
        recent_evaluations = RuleEvaluation.query.filter(
            RuleEvaluation.evaluated_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        blocks = len([e for e in recent_evaluations if e.final_outcome == 'BLOCK'])
        warnings = len([e for e in recent_evaluations if e.final_outcome == 'WARN'])
        
        # Get current compliance issues
        compliance_check = RuleEnforcementService.monitor_system_compliance()
        
        return {
            'active_grants': active_grants,
            'recent_blocks': blocks,
            'recent_warnings': warnings,
            'current_issues': compliance_check['total_issues'],
            'critical_issues': len([i for i in compliance_check['issues'] if i.get('severity') == 'CRITICAL']),
            'last_checked': compliance_check['checked_at']
        }
