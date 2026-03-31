"""
Burn Rate Service - Real-time burn rate analysis and monitoring
Calculates spending vs. time variance to identify financial health issues
"""

from datetime import datetime, timedelta
from typing import Dict, List
from models import db, Grant, GrantFinancialMetrics, ExpenseClaim, BudgetCategory
from sqlalchemy import func

class BurnRateService:
    """Service for calculating and monitoring burn rate analysis"""
    
    @staticmethod
    def calculate_burn_rate(grant_id: int, force_recalculate: bool = False) -> Dict:
        """
        Calculate burn rate metrics for a grant
        Returns comprehensive burn rate analysis
        """
        grant = Grant.query.get_or_404(grant_id)
        
        # Get or create metrics record
        metrics = GrantFinancialMetrics.query.filter_by(grant_id=grant_id).first()
        if not metrics:
            metrics = GrantFinancialMetrics(grant_id=grant_id)
            db.session.add(metrics)
        
        # Check if we need to recalculate (or force it)
        if not force_recalculate and metrics.last_calculated:
            hours_since_last_calc = (datetime.utcnow() - metrics.last_calculated).total_seconds() / 3600
            if hours_since_last_calc < 6:  # Only recalculate every 6 hours
                return metrics.to_dict()
        
        # Calculate time metrics
        time_metrics = BurnRateService._calculate_time_metrics(grant)
        
        # Calculate budget metrics
        budget_metrics = BurnRateService._calculate_budget_metrics(grant)
        
        # Calculate variance and status
        variance = budget_metrics['spent_percentage'] - time_metrics['elapsed_percentage']
        status = BurnRateService._determine_burn_status(variance)
        
        # Update metrics
        metrics.time_elapsed_percentage = time_metrics['elapsed_percentage']
        metrics.budget_spent_percentage = budget_metrics['spent_percentage']
        metrics.burn_rate_variance = variance
        metrics.burn_rate_status = status
        metrics.last_calculated = datetime.utcnow()
        
        db.session.commit()
        
        return metrics.to_dict()
    
    @staticmethod
    def _calculate_time_metrics(grant: Grant) -> Dict:
        """Calculate time-based metrics"""
        today = datetime.utcnow().date()
        start_date = grant.start_date
        end_date = grant.end_date
        
        if not start_date or not end_date:
            return {'elapsed_percentage': 0, 'remaining_days': 0, 'total_days': 0}
        
        total_days = (end_date - start_date).days
        elapsed_days = (today - start_date).days
        remaining_days = (end_date - today).days
        
        # Handle edge cases
        if total_days <= 0:
            return {'elapsed_percentage': 0, 'remaining_days': 0, 'total_days': 0}
        
        if elapsed_days < 0:
            elapsed_percentage = 0
        elif elapsed_days > total_days:
            elapsed_percentage = 100
        else:
            elapsed_percentage = (elapsed_days / total_days) * 100
        
        return {
            'elapsed_percentage': round(elapsed_percentage, 1),
            'remaining_days': max(0, remaining_days),
            'total_days': total_days,
            'elapsed_days': max(0, elapsed_days)
        }
    
    @staticmethod
    def _calculate_budget_metrics(grant: Grant) -> Dict:
        """Calculate budget-based metrics"""
        total_budget = grant.total_budget
        
        if total_budget <= 0:
            return {'spent_percentage': 0, 'total_spent': 0, 'remaining_budget': 0}
        
        # Calculate total spent from approved expenses
        try:
            total_spent = db.session.query(func.sum(ExpenseClaim.amount)).filter(
                ExpenseClaim.grant_id == grant.id,
                ExpenseClaim.status == 'approved'
            ).scalar() or 0
        except:
            # If ExpenseClaim table doesn't exist or has issues
            total_spent = 0
        
        spent_percentage = (total_spent / total_budget) * 100
        remaining_budget = total_budget - total_spent
        
        return {
            'spent_percentage': round(spent_percentage, 1),
            'total_spent': round(total_spent, 2),
            'remaining_budget': round(remaining_budget, 2)
        }
    
    @staticmethod
    def _determine_burn_status(variance: float) -> str:
        """Determine burn rate status based on variance"""
        if variance > 15:
            return 'OVER_SPENDING'
        elif variance < -15:
            return 'UNDER_SPENDING'
        else:
            return 'ON_TRACK'
    
    @staticmethod
    def get_burn_rate_trends(grant_id: int, days: int = 90) -> Dict:
        """Get burn rate trends over time"""
        # For now, return current metrics with trend indicators
        # In a full implementation, this would use historical data
        
        metrics = BurnRateService.calculate_burn_rate(grant_id)
        
        # Simulate trend calculation (would use historical data in production)
        variance = metrics.get('burn_rate_variance', 0)
        
        if variance > 20:
            trend = 'WORSENING'
        elif variance < -20:
            trend = 'IMPROVING'
        else:
            trend = 'STABLE'
        
        return {
            'current_metrics': metrics,
            'trend': trend,
            'period_days': days,
            'recommendations': BurnRateService._generate_burn_recommendations(metrics)
        }
    
    @staticmethod
    def _generate_burn_recommendations(metrics: Dict) -> List[Dict]:
        """Generate recommendations based on burn rate status"""
        recommendations = []
        status = metrics.get('burn_rate_status', 'ON_TRACK')
        variance = metrics.get('burn_rate_variance', 0)
        time_elapsed = metrics.get('time_elapsed_percentage', 0)
        budget_spent = metrics.get('budget_spent_percentage', 0)
        
        if status == 'OVER_SPENDING':
            recommendations.append({
                'type': 'WARNING',
                'priority': 'HIGH',
                'title': 'Over-spending Detected',
                'message': f"You are spending {abs(variance):.1f}% faster than your timeline allows.",
                'action': 'Review upcoming expenses and consider delaying non-essential purchases.',
                'metrics': {
                    'time_elapsed': f"{time_elapsed}%",
                    'budget_spent': f"{budget_spent}%",
                    'variance': f"+{variance:.1f}%"
                }
            })
            
            # Additional recommendations for severe over-spending
            if variance > 30:
                recommendations.append({
                    'type': 'CRITICAL',
                    'priority': 'URGENT',
                    'title': 'Critical Over-spending Alert',
                    'message': f"Your spending rate is {variance:.1f}% ahead of schedule.",
                    'action': 'Immediate budget review required. Consider postponing major purchases.',
                    'metrics': {
                        'risk_level': 'HIGH',
                        'projected_shortfall': 'Calculate projected shortfall'
                    }
                })
                
        elif status == 'UNDER_SPENDING':
            recommendations.append({
                'type': 'INFO',
                'priority': 'MEDIUM',
                'title': 'Under-spending Detected',
                'message': f"You are spending {abs(variance):.1f}% slower than your timeline allows.",
                'action': 'Ensure you are on track to complete project milestones and avoid returning unspent funds.',
                'metrics': {
                    'time_elapsed': f"{time_elapsed}%",
                    'budget_spent': f"{budget_spent}%",
                    'variance': f"{variance:.1f}%"
                }
            })
            
            # Additional recommendations for severe under-spending
            if variance < -30:
                recommendations.append({
                    'type': 'WARNING',
                    'priority': 'HIGH',
                    'title': 'Significant Under-spending',
                    'message': f"Your spending rate is {abs(variance):.1f}% behind schedule.",
                    'action': 'Review project timeline and ensure planned expenses can be executed.',
                    'metrics': {
                        'risk_level': 'MODERATE',
                        'fund_return_risk': 'High'
                    }
                })
        else:
            recommendations.append({
                'type': 'SUCCESS',
                'priority': 'LOW',
                'title': 'On Track',
                'message': 'Your spending pace is well-aligned with your timeline.',
                'action': 'Continue monitoring your burn rate regularly.',
                'metrics': {
                    'time_elapsed': f"{time_elapsed}%",
                    'budget_spent': f"{budget_spent}%",
                    'variance': f"{variance:.1f}%"
                }
            })
        
        # Time-based recommendations
        if time_elapsed > 80:
            recommendations.append({
                'type': 'INFO',
                'priority': 'MEDIUM',
                'title': 'Project Near Completion',
                'message': f"Project is {time_elapsed:.1f}% complete.",
                'action': 'Plan for final expenses and ensure all obligations are met.',
                'metrics': {
                    'completion_stage': 'Final phase'
                }
            })
        
        return recommendations
    
    @staticmethod
    def get_system_burn_rate_summary() -> Dict:
        """Get burn rate summary across all active grants"""
        try:
            active_grants = Grant.query.filter(Grant.status.in_(['active', 'pending'])).all()
        except:
            # If status filter doesn't work, get all grants
            active_grants = Grant.query.all()
        
        summary = {
            'total_grants': len(active_grants),
            'over_spending': 0,
            'under_spending': 0,
            'on_track': 0,
            'average_variance': 0,
            'critical_grants': [],
            'calculation_time': datetime.utcnow().isoformat()
        }
        
        total_variance = 0
        valid_grants = 0
        critical_variance_threshold = 25  # %
        
        for grant in active_grants:
            try:
                metrics = BurnRateService.calculate_burn_rate(grant.id)
                status = metrics.get('burn_rate_status', 'ON_TRACK')
                variance = metrics.get('burn_rate_variance', 0)
                
                # Count status
                if status == 'OVER_SPENDING':
                    summary['over_spending'] += 1
                elif status == 'UNDER_SPENDING':
                    summary['under_spending'] += 1
                else:
                    summary['on_track'] += 1
                
                total_variance += abs(variance)
                valid_grants += 1
                
                # Check for critical cases
                if abs(variance) > critical_variance_threshold:
                    summary['critical_grants'].append({
                        'grant_id': grant.id,
                        'grant_title': grant.title,
                        'variance': variance,
                        'status': status,
                        'time_elapsed': metrics.get('time_elapsed_percentage', 0),
                        'budget_spent': metrics.get('budget_spent_percentage', 0)
                    })
            except Exception as e:
                print(f"Error calculating burn rate for grant {grant.id}: {e}")
                continue
        
        if valid_grants > 0:
            summary['average_variance'] = round(total_variance / valid_grants, 1)
        
        # Sort critical grants by variance severity
        summary['critical_grants'].sort(key=lambda x: abs(x['variance']), reverse=True)
        
        return summary
    
    @staticmethod
    def get_burn_rate_alerts() -> List[Dict]:
        """Get grants that need immediate attention based on burn rate"""
        summary = BurnRateService.get_system_burn_rate_summary()
        alerts = []
        
        # Critical over-spending alerts
        for grant in summary['critical_grants']:
            if grant['variance'] > 25:
                alerts.append({
                    'type': 'CRITICAL',
                    'priority': 'URGENT',
                    'grant_id': grant['grant_id'],
                    'grant_title': grant['grant_title'],
                    'message': f"Critical over-spending: {grant['variance']:.1f}% ahead of schedule",
                    'variance': grant['variance'],
                    'status': grant['status'],
                    'action_required': 'Immediate budget review and spending control measures'
                })
            elif grant['variance'] < -25:
                alerts.append({
                    'type': 'WARNING',
                    'priority': 'HIGH',
                    'grant_id': grant['grant_id'],
                    'grant_title': grant['grant_title'],
                    'message': f"Significant under-spending: {abs(grant['variance']):.1f}% behind schedule",
                    'variance': grant['variance'],
                    'status': grant['status'],
                    'action_required': 'Review project execution and spending plans'
                })
        
        # System-level alerts
        if summary['over_spending'] > (summary['total_grants'] * 0.3):  # More than 30% over-spending
            alerts.append({
                'type': 'SYSTEM',
                'priority': 'HIGH',
                'message': f"System-wide concern: {summary['over_spending']}/{summary['total_grants']} grants are over-spending",
                'metric': f"{round(summary['over_spending'] / summary['total_grants'] * 100, 1)}%",
                'action_required': 'Review institutional spending patterns and provide guidance'
            })
        
        return alerts
    
    @staticmethod
    def calculate_projected_completion(grant_id: int) -> Dict:
        """Calculate projected completion based on current burn rate"""
        grant = Grant.query.get_or_404(grant_id)
        metrics = BurnRateService.calculate_burn_rate(grant_id)
        
        time_elapsed = metrics.get('time_elapsed_percentage', 0) / 100
        budget_spent = metrics.get('budget_spent_percentage', 0) / 100
        
        if budget_spent <= 0:
            return {
                'projected_completion': 'UNKNOWN',
                'months_remaining': None,
                'confidence': 'LOW'
            }
        
        # Calculate projected completion based on spending rate
        spending_rate = budget_spent / time_elapsed if time_elapsed > 0 else 0
        
        if spending_rate == 0:
            return {
                'projected_completion': 'UNKNOWN',
                'months_remaining': None,
                'confidence': 'LOW'
            }
        
        # Project when budget will be depleted
        remaining_budget_percentage = 1 - budget_spent
        projected_time_to_complete = remaining_budget_percentage / spending_rate
        
        total_projected_time = time_elapsed + projected_time_to_complete
        
        # Convert to months
        today = datetime.utcnow().date()
        if grant.start_date and grant.end_date:
            total_days = (grant.end_date - grant.start_date).days
            projected_end_date = grant.start_date + timedelta(days=int(total_days * total_projected_time))
            months_remaining = (projected_end_date - today).days / 30.44
        else:
            months_remaining = None
        
        # Determine confidence level
        variance = abs(metrics.get('burn_rate_variance', 0))
        if variance < 10:
            confidence = 'HIGH'
        elif variance < 20:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return {
            'projected_completion': f"{round(total_projected_time * 100, 1)}%",
            'months_remaining': round(months_remaining, 1) if months_remaining else None,
            'confidence': confidence,
            'spending_rate': round(spending_rate, 2),
            'variance': metrics.get('burn_rate_variance', 0)
        }
