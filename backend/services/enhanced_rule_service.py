"""
Enhanced Rule Service - Provides advanced rule evaluation with context awareness,
machine learning insights, and predictive compliance monitoring.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models import db, Rule, FunderProfile, RuleEvaluation, Grant, ExpenseClaim, GrantTeam, BudgetCategory
from services.rule_service import RuleService

class EnhancedRuleService:
    """Advanced rule evaluation with enhanced system control capabilities"""
    
    @staticmethod
    def evaluate_with_context(action_type: str, context: Dict, grant_id: int, 
                            user_context: Optional[Dict] = None) -> Dict:
        """
        Enhanced evaluation that considers:
        - Historical patterns
        - User behavior
        - Grant-specific context
        - Predictive risk assessment
        """
        # Get base evaluation
        base_result = RuleService.evaluate_action(action_type, context, grant_id, commit=False)
        
        # Enhance with context awareness
        enhanced_result = EnhancedRuleService._add_context_insights(
            base_result, context, grant_id, user_context
        )
        
        # Add predictive risk assessment
        risk_assessment = EnhancedRuleService._assess_predictive_risk(
            action_type, context, grant_id
        )
        enhanced_result['risk_assessment'] = risk_assessment
        
        # Add compliance recommendations
        recommendations = EnhancedRuleService._generate_compliance_recommendations(
            enhanced_result, context, grant_id
        )
        enhanced_result['recommendations'] = recommendations
        
        return enhanced_result
    
    @staticmethod
    def _add_context_insights(base_result: Dict, context: Dict, grant_id: int, 
                            user_context: Optional[Dict]) -> Dict:
        """Add contextual insights to the base evaluation"""
        grant = Grant.query.get(grant_id)
        if not grant:
            return base_result
        
        # Historical compliance score
        compliance_score = EnhancedRuleService._calculate_compliance_score(grant_id)
        
        # Budget utilization context
        budget_utilization = EnhancedRuleService._get_budget_utilization(grant_id)
        
        # User behavior patterns (if user context provided)
        user_behavior = None
        if user_context:
            user_behavior = EnhancedRuleService._analyze_user_behavior(
                user_context.get('user_id'), grant_id
            )
        
        # Time-based context
        time_context = EnhancedRuleService._get_time_context(grant)
        
        enhanced_result = base_result.copy()
        enhanced_result['context_insights'] = {
            'compliance_score': compliance_score,
            'budget_utilization': budget_utilization,
            'user_behavior': user_behavior,
            'time_context': time_context,
            'grant_risk_level': EnhancedRuleService._assess_grant_risk_level(grant)
        }
        
        return enhanced_result
    
    @staticmethod
    def _calculate_compliance_score(grant_id: int) -> Dict:
        """Calculate historical compliance score for a grant"""
        evaluations = RuleEvaluation.query.filter_by(grant_id=grant_id).all()
        
        if not evaluations:
            return {'score': 100, 'total_evaluations': 0, 'blocks': 0}
        
        total_evaluations = len(evaluations)
        blocks = len([e for e in evaluations if e.final_outcome == 'BLOCK'])
        warnings = len([e for e in evaluations if e.final_outcome == 'WARN'])
        
        # Score calculation: 100 - (blocks * 10) - (warnings * 2)
        score = max(0, 100 - (blocks * 10) - (warnings * 2))
        
        return {
            'score': score,
            'total_evaluations': total_evaluations,
            'blocks': blocks,
            'warnings': warnings,
            'last_block_date': max([e.evaluated_at for e in evaluations if e.final_outcome == 'BLOCK'], default=None)
        }
    
    @staticmethod
    def _get_budget_utilization(grant_id: int) -> Dict:
        """Get current budget utilization context"""
        grant = Grant.query.get(grant_id)
        if not grant:
            return {}
        
        total_spent = sum([c.spent for c in grant.categories])
        total_budget = grant.total_budget
        utilization_rate = (total_spent / total_budget * 100) if total_budget > 0 else 0
        
        # Check for category-level issues
        category_issues = []
        for category in grant.categories:
            spent = sum([e.amount for e in category.expenses if e.status == 'approved'])
            if spent > category.budget_allocation:
                category_issues.append({
                    'category': category.name,
                    'overspend': spent - category.budget_allocation,
                    'utilization': (spent / category.budget_allocation * 100) if category.budget_allocation > 0 else 0
                })
        
        return {
            'total_utilization': utilization_rate,
            'total_spent': total_spent,
            'total_budget': total_budget,
            'category_issues': category_issues,
            'remaining_budget': total_budget - total_spent
        }
    
    @staticmethod
    def _analyze_user_behavior(user_id: int, grant_id: int) -> Dict:
        """Analyze user's historical behavior patterns"""
        user_expenses = ExpenseClaim.query.filter_by(submitted_by=user_id).all()
        grant_expenses = [e for e in user_expenses if e.grant_id == grant_id]
        
        if not grant_expenses:
            return {'pattern': 'new_user', 'rejection_rate': 0, 'avg_expense': 0}
        
        total_expenses = len(grant_expenses)
        rejected_expenses = len([e for e in grant_expenses if e.status == 'rejected'])
        rejection_rate = (rejected_expenses / total_expenses * 100) if total_expenses > 0 else 0
        avg_expense = sum([e.amount for e in grant_expenses]) / total_expenses
        
        # Determine behavior pattern
        if rejection_rate > 30:
            pattern = 'high_risk'
        elif rejection_rate > 10:
            pattern = 'moderate_risk'
        else:
            pattern = 'low_risk'
        
        return {
            'pattern': pattern,
            'rejection_rate': rejection_rate,
            'avg_expense': avg_expense,
            'total_expenses': total_expenses
        }
    
    @staticmethod
    def _get_time_context(grant: Grant) -> Dict:
        """Get time-based context for the grant"""
        today = datetime.utcnow().date()
        start_date = grant.start_date
        end_date = grant.end_date
        
        if not start_date or not end_date:
            return {}
        
        total_days = (end_date - start_date).days
        elapsed_days = (today - start_date).days
        remaining_days = (end_date - today).days
        
        progress_percentage = (elapsed_days / total_days * 100) if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'elapsed_days': elapsed_days,
            'remaining_days': remaining_days,
            'progress_percentage': progress_percentage,
            'is_expiring_soon': remaining_days <= 30,
            'is_expired': remaining_days < 0
        }
    
    @staticmethod
    def _assess_grant_risk_level(grant: Grant) -> str:
        """Assess overall risk level for a grant"""
        risk_factors = []
        
        # Budget utilization risk
        total_spent = sum([c.spent for c in grant.categories])
        utilization_rate = (total_spent / grant.total_budget * 100) if grant.total_budget > 0 else 0
        if utilization_rate > 95:
            risk_factors.append('high_utilization')
        elif utilization_rate > 85:
            risk_factors.append('moderate_utilization')
        
        # Time-based risk
        today = datetime.utcnow().date()
        if grant.end_date and (grant.end_date - today).days <= 30:
            risk_factors.append('expiring_soon')
        
        # Compliance history risk
        compliance_score = EnhancedRuleService._calculate_compliance_score(grant.id)
        if compliance_score['score'] < 70:
            risk_factors.append('poor_compliance')
        
        # Determine overall risk level
        if len(risk_factors) >= 3 or 'poor_compliance' in risk_factors:
            return 'HIGH'
        elif len(risk_factors) >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    @staticmethod
    def _assess_predictive_risk(action_type: str, context: Dict, grant_id: int) -> Dict:
        """Assess predictive risk based on patterns and trends"""
        risk_score = 0
        risk_factors = []
        
        # Amount-based risk
        amount = context.get('amount', 0)
        if amount > 1000000:  # MWK 1M
            risk_score += 30
            risk_factors.append('high_amount')
        elif amount > 500000:  # MWK 500K
            risk_score += 15
            risk_factors.append('moderate_amount')
        
        # Category-based risk
        category = context.get('category', '').lower()
        high_risk_categories = ['travel', 'equipment', 'consultant', 'personnel']
        if category in high_risk_categories:
            risk_score += 20
            risk_factors.append('high_risk_category')
        
        # Time-based risk
        grant = Grant.query.get(grant_id)
        if grant and grant.end_date:
            days_remaining = (grant.end_date - datetime.utcnow().date()).days
            if days_remaining < 30:
                risk_score += 25
                risk_factors.append('grant_expiring_soon')
        
        # User behavior risk
        user_id = context.get('user_id')
        if user_id:
            user_behavior = EnhancedRuleService._analyze_user_behavior(user_id, grant_id)
            if user_behavior['pattern'] == 'high_risk':
                risk_score += 20
                risk_factors.append('high_risk_user')
            elif user_behavior['pattern'] == 'moderate_risk':
                risk_score += 10
                risk_factors.append('moderate_risk_user')
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'HIGH'
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'confidence': min(95, 60 + len(risk_factors) * 10)  # Confidence increases with factors
        }
    
    @staticmethod
    def _generate_compliance_recommendations(result: Dict, context: Dict, grant_id: int) -> List[Dict]:
        """Generate actionable compliance recommendations"""
        recommendations = []
        
        # Base recommendations from triggered rules
        for rule in result.get('triggered_rules', []):
            if rule['outcome'] == 'BLOCK':
                recommendations.append({
                    'type': 'REQUIRED_ACTION',
                    'priority': 'HIGH',
                    'title': f"Compliance Required: {rule['name']}",
                    'description': rule['guidance_text'],
                    'action_required': 'Address before proceeding'
                })
            elif rule['outcome'] == 'WARN':
                recommendations.append({
                    'type': 'RECOMMENDATION',
                    'priority': 'MEDIUM',
                    'title': f"Review Recommended: {rule['name']}",
                    'description': rule['guidance_text'],
                    'action_required': 'Consider for optimization'
                })
        
        # Risk-based recommendations
        risk_assessment = result.get('risk_assessment', {})
        if risk_assessment.get('risk_level') == 'HIGH':
            recommendations.append({
                'type': 'RISK_ALERT',
                'priority': 'HIGH',
                'title': 'High Risk Transaction Detected',
                'description': f"Risk score: {risk_assessment.get('risk_score', 0)}",
                'action_required': 'Additional review recommended',
                'risk_factors': risk_assessment.get('risk_factors', [])
            })
        
        # Context-based recommendations
        context_insights = result.get('context_insights', {})
        budget_util = context_insights.get('budget_utilization', {})
        if budget_util.get('category_issues'):
            recommendations.append({
                'type': 'BUDGET_CONCERN',
                'priority': 'MEDIUM',
                'title': 'Budget Category Issues Detected',
                'description': f"{len(budget_util['category_issues'])} categories overspent",
                'action_required': 'Review budget allocation'
            })
        
        # Time-based recommendations
        time_context = context_insights.get('time_context', {})
        if time_context.get('is_expiring_soon'):
            recommendations.append({
                'type': 'TIME_SENSITIVE',
                'priority': 'HIGH',
                'title': 'Grant Expiring Soon',
                'description': f"Only {time_context.get('remaining_days', 0)} days remaining",
                'action_required': 'Expedite remaining activities'
            })
        
        return recommendations
    
    @staticmethod
    def get_compliance_trends(grant_id: int, days: int = 30) -> Dict:
        """Get compliance trends over time"""
        start_date = datetime.utcnow() - timedelta(days=days)
        evaluations = RuleEvaluation.query.filter(
            RuleEvaluation.grant_id == grant_id,
            RuleEvaluation.evaluated_at >= start_date
        ).order_by(RuleEvaluation.evaluated_at).all()
        
        # Group by date
        daily_stats = {}
        for eval in evaluations:
            date_key = eval.evaluated_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {'blocks': 0, 'warnings': 0, 'passes': 0}
            
            if eval.final_outcome == 'BLOCK':
                daily_stats[date_key]['blocks'] += 1
            elif eval.final_outcome == 'WARN':
                daily_stats[date_key]['warnings'] += 1
            else:
                daily_stats[date_key]['passes'] += 1
        
        # Calculate trend
        if len(daily_stats) >= 7:
            recent_week = list(daily_stats.values())[-7:]
            previous_week = list(daily_stats.values())[-14:-7] if len(daily_stats) >= 14 else []
            
            recent_blocks = sum(day['blocks'] for day in recent_week)
            previous_blocks = sum(day['blocks'] for day in previous_week) if previous_week else 0
            
            trend = 'improving' if recent_blocks < previous_blocks else 'declining' if recent_blocks > previous_blocks else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'daily_stats': daily_stats,
            'trend': trend,
            'total_evaluations': len(evaluations),
            'period_days': days
        }
