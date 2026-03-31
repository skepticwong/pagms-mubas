"""
Background task for continuous compliance monitoring
Provides automated rule enforcement and system-wide compliance tracking
"""

import time
import logging
from datetime import datetime, timedelta
from services.rule_enforcement_service import RuleEnforcementService
from services.notification_service import NotificationService
from models import db, Grant, RuleEvaluation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceMonitor:
    """Background task that continuously monitors system compliance"""
    
    def __init__(self, check_interval_minutes: int = 60):
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.running = False
        
    def start_monitoring(self):
        """Start the continuous monitoring process"""
        self.running = True
        logger.info("Starting compliance monitoring...")
        
        while self.running:
            try:
                self.run_compliance_check()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Compliance monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in compliance monitoring: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        logger.info("Compliance monitoring stopped")
    
    def run_compliance_check(self):
        """Run a single compliance check cycle"""
        logger.info(f"Running compliance check at {datetime.utcnow()}")
        
        # Check system-wide compliance
        compliance_result = RuleEnforcementService.monitor_system_compliance()
        
        # Log results
        total_issues = compliance_result['total_issues']
        critical_issues = len([i for i in compliance_result['issues'] if i.get('severity') == 'CRITICAL'])
        high_issues = len([i for i in compliance_result['issues'] if i.get('severity') == 'HIGH'])
        
        logger.info(f"Compliance check completed: {total_issues} issues found "
                   f"({critical_issues} critical, {high_issues} high)")
        
        # Auto-enforce critical violations
        if critical_issues > 0:
            critical_violations = [i for i in compliance_result['issues'] if i.get('severity') == 'CRITICAL']
            enforcement_actions = RuleEnforcementService.enforce_rule_violations(critical_violations)
            logger.info(f"Enforced {len(enforcement_actions)} critical violations")
        
        # Send summary notification if issues found
        if total_issues > 0:
            self.send_compliance_summary(compliance_result)
        
        # Check for grants requiring attention
        self.check_grants_requiring_attention()
        
        # Clean up old evaluation records
        self.cleanup_old_records()
        
        logger.info("Compliance check cycle completed")
    
    def send_compliance_summary(self, compliance_result):
        """Send compliance summary to administrators"""
        issues = compliance_result['issues']
        
        # Group issues by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.get('type', 'UNKNOWN')
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        # Create summary message
        summary = {
            'timestamp': compliance_result['checked_at'],
            'total_issues': len(issues),
            'critical_issues': len([i for i in issues if i.get('severity') == 'CRITICAL']),
            'high_issues': len([i for i in issues if i.get('severity') == 'HIGH']),
            'medium_issues': len([i for i in issues if i.get('severity') == 'MEDIUM']),
            'issue_breakdown': {k: len(v) for k, v in issue_types.items()},
            'affected_grants': len(set(i.get('grant_id') for i in issues if i.get('grant_id')))
        }
        
        # Here you would send this to your notification system
        # For now, we'll just log it
        logger.warning(f"Compliance Summary: {summary}")
        
        # You could also send email, Slack notification, etc.
        # NotificationService.notify_admins('COMPLIANCE_SUMMARY', summary)
    
    def check_grants_requiring_attention(self):
        """Check for grants that require immediate attention"""
        today = datetime.utcnow().date()
        
        # Find grants expiring in next 7 days
        expiring_grants = Grant.query.filter(
            Grant.end_date <= today + timedelta(days=7),
            Grant.end_date >= today,
            Grant.status.in_(['active', 'pending'])
        ).all()
        
        for grant in expiring_grants:
            days_remaining = (grant.end_date - today).days
            if days_remaining <= 7:
                logger.warning(f"Grant {grant.id} ({grant.title}) expires in {days_remaining} days")
                
                # Check if there are pending expenses
                pending_expenses = len([e for e in grant.expenses if e.status == 'pending'])
                if pending_expenses > 0:
                    logger.warning(f"Grant {grant.id} has {pending_expenses} pending expenses")
        
        # Find grants with high budget utilization
        high_utilization_grants = []
        for grant in Grant.query.filter(Grant.status.in_(['active', 'pending'])).all():
            total_spent = sum([c.spent for c in grant.categories])
            utilization_rate = (total_spent / grant.total_budget * 100) if grant.total_budget > 0 else 0
            
            if utilization_rate > 95:
                high_utilization_grants.append({
                    'grant_id': grant.id,
                    'title': grant.title,
                    'utilization': utilization_rate,
                    'remaining': grant.total_budget - total_spent
                })
        
        if high_utilization_grants:
            logger.warning(f"Found {len(high_utilization_grants)} grants with >95% budget utilization")
    
    def cleanup_old_records(self):
        """Clean up old evaluation records to maintain database performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=365)  # Keep 1 year of data
        
        old_evaluations = RuleEvaluation.query.filter(
            RuleEvaluation.evaluated_at < cutoff_date
        ).count()
        
        if old_evaluations > 0:
            logger.info(f"Cleaning up {old_evaluations} old evaluation records")
            # In production, you might want to archive these instead of deleting
            # RuleEvaluation.query.filter(RuleEvaluation.evaluated_at < cutoff_date).delete()
            # db.session.commit()
    
    def get_monitoring_status(self):
        """Get current monitoring status"""
        return {
            'running': self.running,
            'check_interval_minutes': self.check_interval / 60,
            'last_check': getattr(self, 'last_check_time', None),
            'total_checks': getattr(self, 'total_checks', 0)
        }

# Singleton instance
monitor = ComplianceMonitor()

def start_compliance_monitoring():
    """Start the compliance monitoring in a background process"""
    import threading
    
    def run_monitor():
        monitor.start_monitoring()
    
    thread = threading.Thread(target=run_monitor, daemon=True)
    thread.start()
    
    return monitor

if __name__ == "__main__":
    # For testing purposes
    monitor = ComplianceMonitor(check_interval_minutes=5)  # Check every 5 minutes for testing
    monitor.start_monitoring()
