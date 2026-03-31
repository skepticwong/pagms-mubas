"""
Budget Forecasting Service - Financial projections and risk assessment
Calculates projected final spend and remaining balance with risk analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List
from models import db, Grant, GrantFinancialMetrics, ExpenseClaim, GrantTeam, BudgetCategory
from sqlalchemy import func

class BudgetForecastingService:
    """Service for budget forecasting and financial projections"""
    
    @staticmethod
    def calculate_forecast(grant_id: int, force_recalculate: bool = False) -> Dict:
        """
        Calculate comprehensive budget forecast for a grant
        """
        grant = Grant.query.get_or_404(grant_id)
        
        # Get or create metrics record
        metrics = GrantFinancialMetrics.query.filter_by(grant_id=grant_id).first()
        if not metrics:
            metrics = GrantFinancialMetrics(grant_id=grant_id)
            db.session.add(metrics)
        
        # Calculate forecast components
        current_spend = BudgetForecastingService._get_current_spend(grant)
        pending_expenses = BudgetForecastingService._get_pending_expenses(grant)
        recurring_costs = BudgetForecastingService._get_recurring_costs(grant)
        approved_orders = BudgetForecastingService._get_approved_orders(grant)
        
        # Calculate projections
        projected_final_spend = current_spend + pending_expenses + recurring_costs + approved_orders
        projected_remaining_balance = grant.total_budget - projected_final_spend
        
        # Determine forecast status
        forecast_status = BudgetForecastingService._determine_forecast_status(
            projected_remaining_balance, grant.total_budget
        )
        
        # Calculate risk factors
        risk_analysis = BudgetForecastingService._analyze_forecast_risks(
            grant, current_spend, projected_final_spend, projected_remaining_balance
        )
        
        # Update metrics
        metrics.projected_final_spend = projected_final_spend
        metrics.projected_remaining_balance = projected_remaining_balance
        metrics.forecast_status = forecast_status
        metrics.pending_expenses_total = pending_expenses
        metrics.approved_purchase_orders_total = approved_orders
        metrics.recurring_monthly_costs = recurring_costs
        metrics.risk_score = risk_analysis['risk_score']
        metrics.risk_factors = risk_analysis['risk_factors']
        metrics.last_calculated = datetime.utcnow()
        
        db.session.commit()
        
        return metrics.to_dict()
    
    @staticmethod
    def _get_current_spend(grant: Grant) -> float:
        """Get current total spend from approved expenses"""
        try:
            return db.session.query(func.sum(ExpenseClaim.amount)).filter(
                ExpenseClaim.grant_id == grant.id,
                ExpenseClaim.status == 'approved'
            ).scalar() or 0
        except:
            return 0
    
    @staticmethod
    def _get_pending_expenses(grant: Grant) -> float:
        """Get total pending expenses (submitted but not yet approved)"""
        try:
            return db.session.query(func.sum(ExpenseClaim.amount)).filter(
                ExpenseClaim.grant_id == grant.id,
                ExpenseClaim.status.in_(['pending', 'submitted'])
            ).scalar() or 0
        except:
            return 0
    
    @staticmethod
    def _get_recurring_costs(grant: Grant) -> float:
        """Calculate monthly recurring costs (primarily personnel)"""
        monthly_total = 0
        
        try:
            # Get active team members with their salaries
            active_members = GrantTeam.query.filter_by(
                grant_id=grant.id,
                status='active'
            ).all()
            
            for member in active_members:
                if member.pay_rate:
                    # Assume monthly rate (would need adjustment based on how pay_rate is stored)
                    monthly_total += member.pay_rate
        except:
            # If GrantTeam doesn't exist or has issues
            pass
        
        # Project for remaining grant period
        today = datetime.utcnow().date()
        remaining_months = 0
        if grant.end_date and grant.end_date > today:
            remaining_months = (grant.end_date - today).days / 30.44  # Average month length
        
        return monthly_total * max(0, remaining_months)
    
    @staticmethod
    def _get_approved_orders(grant: Grant) -> float:
        """Get total approved purchase orders (encumbrances)"""
        # This would integrate with a purchase order system
        # For now, return 0 (would be implemented based on your PO system)
        return 0
    
    @staticmethod
    def _determine_forecast_status(projected_remaining_balance: float, total_budget: float) -> str:
        """Determine forecast status based on projected remaining balance"""
        if projected_remaining_balance < 0:
            return 'DEFICIT'
        elif projected_remaining_balance < (total_budget * 0.1):  # Less than 10% remaining
            return 'TIGHT'
        else:
            return 'HEALTHY'
    
    @staticmethod
    def _analyze_forecast_risks(grant: Grant, current_spend: float, 
                               projected_spend: float, remaining_balance: float) -> Dict:
        """Analyze risks associated with the forecast"""
        risk_factors = []
        risk_score = 0
        
        # Risk 1: Deficit
        if remaining_balance < 0:
            risk_factors.append('PROJECTED_DEFICIT')
            risk_score += 40
        
        # Risk 2: Tight budget
        elif remaining_balance < (grant.total_budget * 0.05):
            risk_factors.append('VERY_TIGHT_BUDGET')
            risk_score += 25
        
        # Risk 3: High pending expenses
        pending_ratio = (projected_spend - current_spend) / grant.total_budget if grant.total_budget > 0 else 0
        if pending_ratio > 0.3:  # More than 30% pending
            risk_factors.append('HIGH_PENDING_EXPENSES')
            risk_score += 15
        
        # Risk 4: Time running out with high spend rate
        today = datetime.utcnow().date()
        if grant.end_date and grant.end_date > today:
            remaining_days = (grant.end_date - today).days
            if remaining_days > 0:
                daily_spend_rate = current_spend / max(1, (today - grant.start_date).days)
                
                if remaining_days < 30 and daily_spend_rate > 0:
                    projected_daily_spend = remaining_balance / remaining_days
                    if projected_daily_spend < daily_spend_rate * 0.5:
                        risk_factors.append('SPENDING_RATE_MISMATCH')
                        risk_score += 20
        
        # Risk 5: Grant expiring soon with significant pending expenses
        if grant.end_date:
            days_until_expiry = (grant.end_date - today).days
            if days_until_expiry < 60:
                if (projected_spend - current_spend) > (grant.total_budget * 0.2):
                    risk_factors.append('TIME_PRESSURE')
                    risk_score += 15
        
        # Risk 6: No financial buffer
        buffer_percentage = remaining_balance / grant.total_budget if grant.total_budget > 0 else 0
        if buffer_percentage < 0.05:  # Less than 5% buffer
            risk_factors.append('NO_FINANCIAL_BUFFER')
            risk_score += 10
        
        return {
            'risk_score': min(100, risk_score),
            'risk_factors': risk_factors
        }
    
    @staticmethod
    def what_if_scenario(grant_id: int, scenario_changes: Dict) -> Dict:
        """
        Calculate 'what-if' scenarios for planning purposes
        scenario_changes example:
        {
            'new_personnel': [{'pay_rate': 50000, 'months': 6}],
            'equipment_purchase': 15000,
            'travel_increase': 5000
        }
        """
        # Get current forecast as baseline
        current_forecast = BudgetForecastingService.calculate_forecast(grant_id)
        
        # Apply scenario changes
        additional_costs = 0
        
        # New personnel costs
        if 'new_personnel' in scenario_changes:
            for person in scenario_changes['new_personnel']:
                additional_costs += person.get('pay_rate', 0) * person.get('months', 0)
        
        # Equipment purchases
        additional_costs += scenario_changes.get('equipment_purchase', 0)
        
        # Travel increases
        additional_costs += scenario_changes.get('travel_increase', 0)
        
        # Other costs
        additional_costs += scenario_changes.get('other_costs', 0)
        
        # Calculate new projections
        grant = Grant.query.get(grant_id)
        new_projected_spend = current_forecast['projected_final_spend'] + additional_costs
        new_remaining_balance = grant.total_budget - new_projected_spend
        new_status = BudgetForecastingService._determine_forecast_status(
            new_remaining_balance, grant.total_budget
        )
        
        # Calculate new risk factors
        current_spend = current_forecast.get('projected_final_spend', 0) - current_forecast.get('pending_expenses_total', 0)
        new_risk_analysis = BudgetForecastingService._analyze_forecast_risks(
            grant, current_spend, new_projected_spend, new_remaining_balance
        )
        
        return {
            'baseline_forecast': current_forecast,
            'scenario_changes': scenario_changes,
            'additional_costs': additional_costs,
            'new_projected_spend': round(new_projected_spend, 2),
            'new_remaining_balance': round(new_remaining_balance, 2),
            'new_forecast_status': new_status,
            'new_risk_score': new_risk_analysis['risk_score'],
            'new_risk_factors': new_risk_analysis['risk_factors'],
            'impact': {
                'budget_change': -additional_costs,
                'status_change': current_forecast['forecast_status'] != new_status,
                'risk_increase': new_risk_analysis['risk_score'] > current_forecast.get('risk_score', 0),
                'deficit_created': new_remaining_balance < 0
            },
            'recommendations': BudgetForecastingService._generate_scenario_recommendations(
                current_forecast, new_remaining_balance, new_status
            )
        }
    
    @staticmethod
    def _generate_scenario_recommendations(baseline: Dict, new_balance: float, new_status: str) -> List[Dict]:
        """Generate recommendations based on scenario analysis"""
        recommendations = []
        
        if new_status == 'DEFICIT':
            recommendations.append({
                'type': 'CRITICAL',
                'priority': 'URGENT',
                'title': 'Deficit Projected',
                'message': f"This scenario creates a deficit of ${abs(new_balance):,.2f}",
                'action': 'Reduce costs or find additional funding sources'
            })
        elif new_status == 'TIGHT':
            recommendations.append({
                'type': 'WARNING',
                'priority': 'HIGH',
                'title': 'Budget Will Be Tight',
                'message': f"Only ${new_balance:,.2f} remaining under this scenario",
                'action': 'Monitor expenses closely and prioritize essential spending'
            })
        else:
            recommendations.append({
                'type': 'INFO',
                'priority': 'LOW',
                'title': 'Financially Viable',
                'message': f"Scenario maintains healthy balance of ${new_balance:,.2f}",
                'action': 'Proceed with planned spending'
            })
        
        return recommendations
    
    @staticmethod
    def get_forecast_summary() -> Dict:
        """Get forecast summary across all active grants"""
        try:
            active_grants = Grant.query.filter(Grant.status.in_(['active', 'pending'])).all()
        except:
            active_grants = Grant.query.all()
        
        summary = {
            'total_grants': len(active_grants),
            'healthy': 0,
            'tight': 0,
            'deficit': 0,
            'total_projected_spend': 0,
            'total_remaining_balance': 0,
            'high_risk_grants': [],
            'average_risk_score': 0,
            'calculation_time': datetime.utcnow().isoformat()
        }
        
        total_risk_score = 0
        valid_grants = 0
        
        for grant in active_grants:
            try:
                forecast = BudgetForecastingService.calculate_forecast(grant.id)
                status = forecast.get('forecast_status', 'HEALTHY')
                risk_score = forecast.get('risk_score', 0)
                
                # Count status
                if status == 'HEALTHY':
                    summary['healthy'] += 1
                elif status == 'TIGHT':
                    summary['tight'] += 1
                else:
                    summary['deficit'] += 1
                
                summary['total_projected_spend'] += forecast.get('projected_final_spend', 0)
                summary['total_remaining_balance'] += forecast.get('projected_remaining_balance', 0)
                
                total_risk_score += risk_score
                valid_grants += 1
                
                # Check for high risk grants
                if risk_score > 70:
                    summary['high_risk_grants'].append({
                        'grant_id': grant.id,
                        'grant_title': grant.title,
                        'risk_score': risk_score,
                        'forecast_status': status,
                        'risk_factors': forecast.get('risk_factors', []),
                        'projected_remaining': forecast.get('projected_remaining_balance', 0)
                    })
            except Exception as e:
                print(f"Error calculating forecast for grant {grant.id}: {e}")
                continue
        
        if valid_grants > 0:
            summary['average_risk_score'] = round(total_risk_score / valid_grants, 1)
        
        # Sort high risk grants by risk score
        summary['high_risk_grants'].sort(key=lambda x: x['risk_score'], reverse=True)
        
        return summary
    
    @staticmethod
    def get_financial_health_indicators(grant_id: int) -> Dict:
        """Get comprehensive financial health indicators for a grant"""
        forecast = BudgetForecastingService.calculate_forecast(grant_id)
        
        # Calculate additional indicators
        grant = Grant.query.get(grant_id)
        
        # Budget utilization
        current_spend = forecast.get('projected_final_spend', 0) - forecast.get('pending_expenses_total', 0)
        utilization_rate = (current_spend / grant.total_budget * 100) if grant.total_budget > 0 else 0
        
        # Runway (months remaining at current spend rate)
        today = datetime.utcnow().date()
        if grant.end_date and grant.end_date > today:
            remaining_months = (grant.end_date - today).days / 30.44
        else:
            remaining_months = 0
        
        # Financial stress indicators
        stress_indicators = []
        
        # Check if spending is accelerating
        if forecast.get('pending_expenses_total', 0) > (grant.total_budget * 0.2):
            stress_indicators.append('HIGH_PENDING_COMMITMENTS')
        
        # Check if buffer is insufficient
        buffer_months = forecast.get('projected_remaining_balance', 0) / (current_spend / remaining_months) if remaining_months > 0 and current_spend > 0 else 0
        if buffer_months < 1:
            stress_indicators.append('INSUFFICIENT_BUFFER')
        
        # Check risk level
        risk_score = forecast.get('risk_score', 0)
        if risk_score > 70:
            stress_indicators.append('HIGH_RISK_SCORE')
        
        return {
            'forecast': forecast,
            'utilization_rate': round(utilization_rate, 1),
            'remaining_months': round(remaining_months, 1),
            'buffer_months': round(buffer_months, 1),
            'stress_indicators': stress_indicators,
            'health_score': BudgetForecastingService._calculate_health_score(forecast, utilization_rate, buffer_months),
            'recommendations': BudgetForecastingService._generate_health_recommendations(
                forecast, utilization_rate, buffer_months, stress_indicators
            )
        }
    
    @staticmethod
    def _calculate_health_score(forecast: Dict, utilization_rate: float, buffer_months: float) -> int:
        """Calculate overall financial health score (0-100)"""
        score = 100
        
        # Deduct points for poor forecast status
        status = forecast.get('forecast_status', 'HEALTHY')
        if status == 'DEFICIT':
            score -= 50
        elif status == 'TIGHT':
            score -= 25
        
        # Deduct points for high risk score
        risk_score = forecast.get('risk_score', 0)
        score -= min(30, risk_score // 2)
        
        # Deduct points for poor utilization
        if utilization_rate > 95:
            score -= 20
        elif utilization_rate < 50:
            score -= 10
        
        # Deduct points for insufficient buffer
        if buffer_months < 1:
            score -= 15
        elif buffer_months < 2:
            score -= 5
        
        return max(0, score)
    
    @staticmethod
    def _generate_health_recommendations(forecast: Dict, utilization_rate: float, 
                                      buffer_months: float, stress_indicators: List[str]) -> List[Dict]:
        """Generate health-based recommendations"""
        recommendations = []
        
        # Status-based recommendations
        status = forecast.get('forecast_status', 'HEALTHY')
        if status == 'DEFICIT':
            recommendations.append({
                'type': 'CRITICAL',
                'priority': 'URGENT',
                'title': 'Deficit Alert',
                'message': 'Projected spending exceeds available budget',
                'action': 'Immediate cost reduction measures required'
            })
        elif status == 'TIGHT':
            recommendations.append({
                'type': 'WARNING',
                'priority': 'HIGH',
                'title': 'Budget Tight',
                'message': 'Limited financial buffer remaining',
                'action': 'Review and prioritize upcoming expenses'
            })
        
        # Utilization-based recommendations
        if utilization_rate > 95:
            recommendations.append({
                'type': 'WARNING',
                'priority': 'HIGH',
                'title': 'High Budget Utilization',
                'message': f'{utilization_rate:.1f}% of budget already utilized',
                'action': 'Carefully review all remaining expenses'
            })
        elif utilization_rate < 50:
            recommendations.append({
                'type': 'INFO',
                'priority': 'MEDIUM',
                'title': 'Low Utilization',
                'message': f'Only {utilization_rate:.1f}% of budget utilized',
                'action': 'Ensure project activities are on track'
            })
        
        # Buffer-based recommendations
        if buffer_months < 1:
            recommendations.append({
                'type': 'WARNING',
                'priority': 'HIGH',
                'title': 'Insufficient Financial Buffer',
                'message': 'Less than 1 month of financial buffer',
                'action': 'Build contingency fund or reduce spending rate'
            })
        
        # Stress indicator recommendations
        if 'HIGH_PENDING_COMMITMENTS' in stress_indicators:
            recommendations.append({
                'type': 'INFO',
                'priority': 'MEDIUM',
                'title': 'High Pending Commitments',
                'message': 'Large amount of expenses pending approval',
                'action': 'Monitor approval workflow and spending impact'
            })
        
        return recommendations
