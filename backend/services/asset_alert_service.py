"""
Asset Alert Service - Alert and notification system for assets
Handles proactive alerts for maintenance, returns, compliance, and other asset events
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Asset, AssetMaintenance, User, Grant
from services.notification_service import NotificationService
from services.asset_rules_service import AssetRulesService

class AssetAlertService:
    """Service for managing asset alerts and notifications"""
    
    @staticmethod
    def generate_all_alerts(grant_id: int = None) -> List[Dict]:
        """Generate all types of alerts for assets"""
        all_alerts = []
        
        # Overdue return alerts
        overdue_returns = AssetAlertService._get_overdue_return_alerts(grant_id)
        all_alerts.extend(overdue_returns)
        
        # Upcoming return alerts
        upcoming_returns = AssetAlertService._get_upcoming_return_alerts(grant_id)
        all_alerts.extend(upcoming_returns)
        
        # Overdue maintenance alerts
        overdue_maintenance = AssetAlertService._get_overdue_maintenance_alerts(grant_id)
        all_alerts.extend(overdue_maintenance)
        
        # Upcoming maintenance alerts
        upcoming_maintenance = AssetAlertService._get_upcoming_maintenance_alerts(grant_id)
        all_alerts.extend(upcoming_maintenance)
        
        # Compliance alerts
        compliance_alerts = AssetAlertService._get_compliance_alerts(grant_id)
        all_alerts.extend(compliance_alerts)
        
        # High-value asset alerts
        high_value_alerts = AssetAlertService._get_high_value_asset_alerts(grant_id)
        all_alerts.extend(high_value_alerts)
        
        # Sort by severity and creation date
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_alerts.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['created_at']), reverse=True)
        
        return all_alerts
    
    @staticmethod
    def _get_overdue_return_alerts(grant_id: int = None) -> List[Dict]:
        """Get alerts for assets with overdue return dates"""
        today = datetime.utcnow().date()
        
        query = Asset.query.filter(
            Asset.expected_return_date < today,
            Asset.status.in_(['ACTIVE', 'LENDED'])
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        overdue_assets = query.all()
        alerts = []
        
        for asset in overdue_assets:
            days_overdue = (today - asset.expected_return_date).days
            
            severity = 'critical' if days_overdue > 30 else 'high' if days_overdue > 14 else 'medium'
            
            alerts.append({
                'id': f"overdue_return_{asset.id}",
                'type': 'overdue_return',
                'severity': severity,
                'title': f'Overdue Return: {asset.name}',
                'message': f'Asset is {days_overdue} days overdue for return to {asset.owner_name or "lender"}',
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_tag': asset.asset_tag,
                'grant_id': asset.grant_id,
                'action_required': 'Return asset immediately or contact lender',
                'due_date': asset.expected_return_date.isoformat(),
                'days_overdue': days_overdue,
                'created_at': datetime.utcnow(),
                'category': 'returns'
            })
        
        return alerts
    
    @staticmethod
    def _get_upcoming_return_alerts(grant_id: int = None) -> List[Dict]:
        """Get alerts for assets with upcoming return dates"""
        today = datetime.utcnow().date()
        warning_period = 7  # Alert 7 days before return
        
        query = Asset.query.filter(
            Asset.expected_return_date <= today + timedelta(days=warning_period),
            Asset.expected_return_date > today,
            Asset.status.in_(['ACTIVE', 'LENDED'])
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        upcoming_assets = query.all()
        alerts = []
        
        for asset in upcoming_assets:
            days_until = (asset.expected_return_date - today).days
            
            alerts.append({
                'id': f"upcoming_return_{asset.id}",
                'type': 'upcoming_return',
                'severity': 'medium',
                'title': f'Upcoming Return: {asset.name}',
                'message': f'Asset return due in {days_until} days',
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_tag': asset.asset_tag,
                'grant_id': asset.grant_id,
                'action_required': 'Schedule return before due date',
                'due_date': asset.expected_return_date.isoformat(),
                'days_until': days_until,
                'created_at': datetime.utcnow(),
                'category': 'returns'
            })
        
        return alerts
    
    @staticmethod
    def _get_overdue_maintenance_alerts(grant_id: int = None) -> List[Dict]:
        """Get alerts for assets with overdue maintenance"""
        today = datetime.utcnow().date()
        
        query = Asset.query.filter(
            Asset.next_maintenance_date < today,
            Asset.status == 'ACTIVE'
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        overdue_assets = query.all()
        alerts = []
        
        for asset in overdue_assets:
            days_overdue = (today - asset.next_maintenance_date).days
            
            severity = 'critical' if days_overdue > 90 else 'high' if days_overdue > 30 else 'medium'
            
            alerts.append({
                'id': f"overdue_maintenance_{asset.id}",
                'type': 'overdue_maintenance',
                'severity': severity,
                'title': f'Overdue Maintenance: {asset.name}',
                'message': f'Maintenance is {days_overdue} days overdue',
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_tag': asset.asset_tag,
                'grant_id': asset.grant_id,
                'action_required': 'Schedule maintenance immediately',
                'due_date': asset.next_maintenance_date.isoformat(),
                'days_overdue': days_overdue,
                'created_at': datetime.utcnow(),
                'category': 'maintenance'
            })
        
        return alerts
    
    @staticmethod
    def _get_upcoming_maintenance_alerts(grant_id: int = None) -> List[Dict]:
        """Get alerts for assets with upcoming maintenance"""
        today = datetime.utcnow().date()
        warning_period = 14  # Alert 14 days before maintenance
        
        query = Asset.query.filter(
            Asset.next_maintenance_date <= today + timedelta(days=warning_period),
            Asset.next_maintenance_date > today,
            Asset.status == 'ACTIVE'
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        upcoming_assets = query.all()
        alerts = []
        
        for asset in upcoming_assets:
            days_until = (asset.next_maintenance_date - today).days
            
            alerts.append({
                'id': f"upcoming_maintenance_{asset.id}",
                'type': 'upcoming_maintenance',
                'severity': 'low',
                'title': f'Upcoming Maintenance: {asset.name}',
                'message': f'Maintenance due in {days_until} days',
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_tag': asset.asset_tag,
                'grant_id': asset.grant_id,
                'action_required': 'Schedule maintenance appointment',
                'due_date': asset.next_maintenance_date.isoformat(),
                'days_until': days_until,
                'created_at': datetime.utcnow(),
                'category': 'maintenance'
            })
        
        return alerts
    
    @staticmethod
    def _get_compliance_alerts(grant_id: int = None) -> List[Dict]:
        """Get compliance-related alerts"""
        alerts = []
        
        # Get compliance alerts from rules service
        compliance_alerts = AssetRulesService.AssetComplianceMonitor.get_compliance_alerts(grant_id)
        
        for alert in compliance_alerts:
            # Map severity
            severity_map = {'high': 'high', 'medium': 'medium', 'low': 'low'}
            severity = severity_map.get(alert['severity'], 'medium')
            
            alerts.append({
                'id': f"compliance_{alert['asset_id']}_{alert['issue_type']}",
                'type': 'compliance',
                'severity': severity,
                'title': f'Compliance Issue: {alert["asset_name"]}',
                'message': alert['message'],
                'asset_id': alert['asset_id'],
                'asset_name': alert['asset_name'],
                'asset_tag': alert['asset_tag'],
                'grant_id': alert['grant_id'],
                'action_required': alert['action_required'],
                'created_at': alert['created_at'],
                'category': 'compliance'
            })
        
        return alerts
    
    @staticmethod
    def _get_high_value_asset_alerts(grant_id: int = None) -> List[Dict]:
        """Get alerts for high-value assets that need attention"""
        query = Asset.query.filter(Asset.purchase_cost > 10000, Asset.status == 'ACTIVE')
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        high_value_assets = query.all()
        alerts = []
        
        for asset in high_value_assets:
            # Check if high-value asset needs disposition planning
            grant = Grant.query.get(asset.grant_id)
            if grant:
                days_to_close = None
                if hasattr(grant, 'end_date'):
                    days_to_close = (grant.end_date - datetime.utcnow().date()).days
                
                if days_to_close and days_to_close < 90:
                    alerts.append({
                        'id': f"high_value_disposition_{asset.id}",
                        'type': 'high_value_disposition',
                        'severity': 'medium',
                        'title': f'Disposition Planning: {asset.name}',
                        'message': f'High-value asset (${asset.purchase_cost:,.2f}) requires disposition planning',
                        'asset_id': asset.id,
                        'asset_name': asset.name,
                        'asset_tag': asset.asset_tag,
                        'grant_id': asset.grant_id,
                        'action_required': 'Plan asset disposition before grant closeout',
                        'asset_value': asset.purchase_cost,
                        'days_to_closeout': days_to_close,
                        'created_at': datetime.utcnow(),
                        'category': 'disposition'
                    })
        
        return alerts
    
    @staticmethod
    def get_alert_summary(grant_id: int = None) -> Dict:
        """Get summary of alerts by category and severity"""
        alerts = AssetAlertService.generate_all_alerts(grant_id)
        
        summary = {
            'total_alerts': len(alerts),
            'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'by_category': {
                'returns': 0,
                'maintenance': 0,
                'compliance': 0,
                'disposition': 0
            },
            'upcoming_deadlines': [],
            'overdue_items': []
        }
        
        for alert in alerts:
            # Count by severity
            severity = alert['severity']
            if severity in summary['by_severity']:
                summary['by_severity'][severity] += 1
            
            # Count by category
            category = alert['category']
            if category in summary['by_category']:
                summary['by_category'][category] += 1
            
            # Track upcoming deadlines
            if alert['type'] in ['upcoming_return', 'upcoming_maintenance']:
                summary['upcoming_deadlines'].append(alert)
            
            # Track overdue items
            if alert['type'] in ['overdue_return', 'overdue_maintenance']:
                summary['overdue_items'].append(alert)
        
        # Sort deadlines and overdue items
        summary['upcoming_deadlines'].sort(key=lambda x: x.get('days_until', 999))
        summary['overdue_items'].sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        
        return summary
    
    @staticmethod
    def create_alert_notifications(alerts: List[Dict], user_id: int = None):
        """Create notifications for alerts"""
        notifications_created = 0
        
        for alert in alerts:
            # Only create notifications for high-priority alerts
            if alert['severity'] in ['critical', 'high']:
                # Determine who should receive the notification
                recipients = AssetAlertService._get_alert_recipients(alert, user_id)
                
                for recipient_id in recipients:
                    NotificationService.create_notification(
                        user_id=recipient_id,
                        title=alert['title'],
                        message=alert['message'],
                        type='asset_alert',
                        related_id=alert['asset_id'],
                        metadata={
                            'alert_id': alert['id'],
                            'severity': alert['severity'],
                            'category': alert['category']
                        }
                    )
                    notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def _get_alert_recipients(alert: Dict, requesting_user_id: int = None) -> List[int]:
        """Determine who should receive alert notifications"""
        recipients = []
        
        # Always include the requesting user if specified
        if requesting_user_id:
            recipients.append(requesting_user_id)
        
        # Get asset and grant information
        asset = Asset.query.get(alert['asset_id'])
        if not asset:
            return recipients
        
        grant = Grant.query.get(asset.grant_id)
        if not grant:
            return recipients
        
        # Include grant PI for critical alerts
        if alert['severity'] in ['critical', 'high'] and grant.pi_id:
            recipients.append(grant.pi_id)
        
        # Include asset custodian
        if asset.custodian_user_id and asset.custodian_user_id not in recipients:
            recipients.append(asset.custodian_user_id)
        
        # Include RSU users for critical compliance alerts
        if alert['severity'] == 'critical' and alert['category'] == 'compliance':
            rsu_users = User.query.filter_by(role='RSU').all()
            for rsu_user in rsu_users:
                if rsu_user.id not in recipients:
                    recipients.append(rsu_user.id)
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        return recipients
    
    @staticmethod
    def dismiss_alert(alert_id: str, user_id: int, reason: str = None) -> bool:
        """Dismiss an alert (in production, this would store dismissal records)"""
        # For now, we'll just log the dismissal
        print(f"Alert {alert_id} dismissed by user {user_id}. Reason: {reason or 'No reason provided'}")
        return True
    
    @staticmethod
    def get_alert_trends(grant_id: int, days: int = 30) -> Dict:
        """Get alert trends over time"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # This would typically query alert history from a database
        # For now, we'll return current alerts as a baseline
        current_alerts = AssetAlertService.generate_all_alerts(grant_id)
        
        trends = {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'current_alerts': len(current_alerts),
            'by_severity_trend': {
                'critical': len([a for a in current_alerts if a['severity'] == 'critical']),
                'high': len([a for a in current_alerts if a['severity'] == 'high']),
                'medium': len([a for a in current_alerts if a['severity'] == 'medium']),
                'low': len([a for a in current_alerts if a['severity'] == 'low'])
            },
            'by_category_trend': {
                'returns': len([a for a in current_alerts if a['category'] == 'returns']),
                'maintenance': len([a for a in current_alerts if a['category'] == 'maintenance']),
                'compliance': len([a for a in current_alerts if a['category'] == 'compliance']),
                'disposition': len([a for a in current_alerts if a['category'] == 'disposition'])
            }
        }
        
        return trends
    
    @staticmethod
    def schedule_alert_check(grant_id: int = None):
        """Schedule regular alert checks (in production, this would use a job scheduler)"""
        alerts = AssetAlertService.generate_all_alerts(grant_id)
        
        # Create notifications for high-priority alerts
        notifications_count = AssetAlertService.create_alert_notifications(alerts)
        
        print(f"Alert check completed. Generated {len(alerts)} alerts, created {notifications_count} notifications")
        
        return {
            'alerts_generated': len(alerts),
            'notifications_created': notifications_count,
            'check_time': datetime.utcnow().isoformat()
        }
