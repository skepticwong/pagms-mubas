"""
Asset Audit Service - Comprehensive audit trail system
Tracks all asset-related activities and provides audit reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Asset, AssetMaintenance, AssetTransfer, User, Grant
from services.notification_service import NotificationService

class AssetAuditService:
    """Service for managing asset audit trails"""
    
    @staticmethod
    def create_audit_log(asset_id: int, action: str, details: Dict, user_id: int, ip_address: str = None) -> Dict:
        """Create an audit log entry for asset activity"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Create audit log entry
        audit_log = {
            'id': f"audit_{asset_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'asset_id': asset_id,
            'action': action,
            'details': details,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address,
            'user_agent': details.get('user_agent', ''),
            'session_id': details.get('session_id', ''),
            'old_values': details.get('old_values', {}),
            'new_values': details.get('new_values', {}),
            'impact_level': AssetAuditService._calculate_impact_level(action, details),
            'compliance_flag': AssetAuditService._check_compliance_flag(action, details)
        }
        
        # Store audit log in asset's audit trail
        if not asset.audit_trail:
            asset.audit_trail = []
        
        asset.audit_trail.append(audit_log)
        asset.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Check for suspicious activity
        if audit_log['compliance_flag']:
            AssetAuditService._check_suspicious_activity(audit_log)
        
        return audit_log
    
    @staticmethod
    def get_asset_audit_trail(asset_id: int, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get audit trail for a specific asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        audit_trail = asset.audit_trail or []
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_trail = []
            start = datetime.fromisoformat(start_date) if start_date else datetime.min
            end = datetime.fromisoformat(end_date) if end_date else datetime.max
            
            for entry in audit_trail:
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if start <= entry_date <= end:
                    filtered_trail.append(entry)
            
            audit_trail = filtered_trail
        
        # Sort by timestamp (newest first)
        audit_trail.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return audit_trail
    
    @staticmethod
    def get_grant_audit_trail(grant_id: int, start_date: str = None, end_date: str = None, action_filter: str = None) -> List[Dict]:
        """Get audit trail for all assets in a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        all_audit_entries = []
        
        for asset in assets:
            asset_trail = asset.audit_trail or []
            
            for entry in asset_trail:
                # Add asset context
                entry['asset_name'] = asset.name
                entry['asset_tag'] = asset.asset_tag
                entry['asset_category'] = asset.category
                
                # Filter by date range
                if start_date or end_date:
                    start = datetime.fromisoformat(start_date) if start_date else datetime.min
                    end = datetime.fromisoformat(end_date) if end_date else datetime.max
                    entry_date = datetime.fromisoformat(entry['timestamp'])
                    if not (start <= entry_date <= end):
                        continue
                
                # Filter by action
                if action_filter and entry['action'] != action_filter:
                    continue
                
                all_audit_entries.append(entry)
        
        # Sort by timestamp (newest first)
        all_audit_entries.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return all_audit_entries
    
    @staticmethod
    def get_user_audit_activity(user_id: int, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get audit activity for a specific user"""
        assets = Asset.query.all()
        
        user_activities = []
        
        for asset in assets:
            asset_trail = asset.audit_trail or []
            
            for entry in asset_trail:
                if entry.get('user_id') == user_id:
                    # Add asset context
                    entry['asset_name'] = asset.name
                    entry['asset_tag'] = asset.asset_tag
                    entry['grant_id'] = asset.grant_id
                    
                    # Filter by date range
                    if start_date or end_date:
                        start = datetime.fromisoformat(start_date) if start_date else datetime.min
                        end = datetime.fromisoformat(end_date) if end_date else datetime.max
                        entry_date = datetime.fromisoformat(entry['timestamp'])
                        if not (start <= entry_date <= end):
                            continue
                    
                    user_activities.append(entry)
        
        # Sort by timestamp (newest first)
        user_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return user_activities
    
    @staticmethod
    def generate_audit_report(grant_id: int, report_type: str = 'comprehensive', start_date: str = None, end_date: str = None) -> Dict:
        """Generate comprehensive audit report"""
        audit_trail = AssetAuditService.get_grant_audit_trail(grant_id, start_date, end_date)
        
        report = {
            'report_type': f'Audit Report - {report_type.title()}',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': AssetAuditService._generate_audit_summary(audit_trail),
            'activities_by_action': AssetAuditService._group_activities_by_action(audit_trail),
            'activities_by_user': AssetAuditService._group_activities_by_user(audit_trail),
            'activities_by_asset': AssetAuditService._group_activities_by_asset(audit_trail),
            'compliance_issues': AssetAuditService._identify_compliance_issues(audit_trail),
            'suspicious_activities': AssetAuditService._identify_suspicious_activities(audit_trail),
            'recommendations': []
        }
        
        # Add recommendations based on audit findings
        report['recommendations'] = AssetAuditService._generate_audit_recommendations(report)
        
        return report
    
    @staticmethod
    def get_audit_statistics(grant_id: int, days: int = 30) -> Dict:
        """Get audit statistics for recent activity"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        audit_trail = AssetAuditService.get_grant_audit_trail(
            grant_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        stats = {
            'period_days': days,
            'total_activities': len(audit_trail),
            'unique_users': len(set(entry['user_id'] for entry in audit_trail)),
            'unique_assets': len(set(entry['asset_id'] for entry in audit_trail)),
            'high_impact_activities': len([e for e in audit_trail if e.get('impact_level') == 'high']),
            'compliance_flags': len([e for e in audit_trail if e.get('compliance_flag')]),
            'activities_by_day': AssetAuditService._group_activities_by_day(audit_trail),
            'top_actions': AssetAuditService._get_top_actions(audit_trail),
            'most_active_users': AssetAuditService._get_most_active_users(audit_trail),
            'most_active_assets': AssetAuditService._get_most_active_assets(audit_trail)
        }
        
        return stats
    
    @staticmethod
    def detect_anomalies(grant_id: int, days: int = 30) -> List[Dict]:
        """Detect anomalous activities in audit trail"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        audit_trail = AssetAuditService.get_grant_audit_trail(
            grant_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        anomalies = []
        
        # Check for unusual patterns
        user_activity_counts = {}
        asset_activity_counts = {}
        action_activity_counts = {}
        
        for entry in audit_trail:
            user_id = entry['user_id']
            asset_id = entry['asset_id']
            action = entry['action']
            
            user_activity_counts[user_id] = user_activity_counts.get(user_id, 0) + 1
            asset_activity_counts[asset_id] = asset_activity_counts.get(asset_id, 0) + 1
            action_activity_counts[action] = action_activity_counts.get(action, 0) + 1
        
        # Detect users with unusually high activity
        avg_user_activity = sum(user_activity_counts.values()) / len(user_activity_counts) if user_activity_counts else 0
        for user_id, count in user_activity_counts.items():
            if count > avg_user_activity * 3:  # 3x average activity
                anomalies.append({
                    'type': 'high_user_activity',
                    'user_id': user_id,
                    'activity_count': count,
                    'average_activity': avg_user_activity,
                    'severity': 'medium'
                })
        
        # Detect assets with unusual activity
        avg_asset_activity = sum(asset_activity_counts.values()) / len(asset_activity_counts) if asset_activity_counts else 0
        for asset_id, count in asset_activity_counts.items():
            if count > avg_asset_activity * 3:  # 3x average activity
                anomalies.append({
                    'type': 'high_asset_activity',
                    'asset_id': asset_id,
                    'activity_count': count,
                    'average_activity': avg_asset_activity,
                    'severity': 'medium'
                })
        
        # Check for activities outside business hours
        business_hours_anomalies = AssetAuditService._check_business_hours_anomalies(audit_trail)
        anomalies.extend(business_hours_anomalies)
        
        # Check for rapid successive activities
        rapid_activity_anomalies = AssetAuditService._check_rapid_activities(audit_trail)
        anomalies.extend(rapid_activity_anomalies)
        
        return anomalies
    
    @staticmethod
    def export_audit_trail(grant_id: int, format_type: str = 'json', start_date: str = None, end_date: str = None) -> Dict:
        """Export audit trail in specified format"""
        audit_trail = AssetAuditService.get_grant_audit_trail(grant_id, start_date, end_date)
        
        export_data = {
            'export_type': 'Audit Trail Export',
            'grant_id': grant_id,
            'exported_at': datetime.utcnow().isoformat(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'total_entries': len(audit_trail),
            'audit_trail': audit_trail
        }
        
        if format_type == 'csv':
            return AssetAuditService._convert_audit_to_csv(export_data)
        elif format_type == 'excel':
            return AssetAuditService._convert_audit_to_excel(export_data)
        else:
            return export_data
    
    @staticmethod
    def _calculate_impact_level(action: str, details: Dict) -> str:
        """Calculate impact level of an action"""
        high_impact_actions = [
            'asset_disposed', 'asset_transferred', 'asset_status_changed',
            'document_deleted', 'maintenance_completed', 'custodian_changed'
        ]
        
        medium_impact_actions = [
            'asset_updated', 'document_uploaded', 'maintenance_scheduled',
            'transfer_requested', 'alert_dismissed'
        ]
        
        if action in high_impact_actions:
            return 'high'
        elif action in medium_impact_actions:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def _check_compliance_flag(action: str, details: Dict) -> bool:
        """Check if action requires compliance monitoring"""
        compliance_actions = [
            'asset_disposed', 'asset_transferred', 'asset_status_changed',
            'document_deleted', 'custodian_changed', 'high_value_modification'
        ]
        
        # Check for high-value asset modifications
        if action == 'asset_updated' and details.get('new_values', {}).get('purchase_cost', 0) > 10000:
            return True
        
        return action in compliance_actions
    
    @staticmethod
    def _check_suspicious_activity(audit_log: Dict):
        """Check for suspicious activity patterns"""
        suspicious_patterns = [
            'multiple_status_changes',
            'unusual_access_times',
            'high_frequency_changes',
            'privilege_escalation'
        ]
        
        # This would implement more sophisticated pattern detection
        # For now, just create a notification for compliance-flagged activities
        if audit_log['compliance_flag']:
            # Notify RSU users of compliance-flagged activities
            from models import User
            rsu_users = User.query.filter_by(role='RSU').all()
            
            for rsu_user in rsu_users:
                NotificationService.create_notification(
                    user_id=rsu_user.id,
                    title='Compliance-Flagged Asset Activity',
                    message=f'Asset activity flagged for compliance review: {audit_log["action"]}',
                    type='compliance_alert',
                    related_id=audit_log['asset_id']
                )
    
    @staticmethod
    def _generate_audit_summary(audit_trail: List[Dict]) -> Dict:
        """Generate summary statistics for audit trail"""
        if not audit_trail:
            return {
                'total_activities': 0,
                'unique_users': 0,
                'unique_assets': 0,
                'date_range': None,
                'high_impact_count': 0,
                'compliance_flags': 0
            }
        
        dates = [datetime.fromisoformat(entry['timestamp']).date() for entry in audit_trail]
        
        return {
            'total_activities': len(audit_trail),
            'unique_users': len(set(entry['user_id'] for entry in audit_trail)),
            'unique_assets': len(set(entry['asset_id'] for entry in audit_trail)),
            'date_range': {
                'start': min(dates).isoformat(),
                'end': max(dates).isoformat()
            },
            'high_impact_count': len([e for e in audit_trail if e.get('impact_level') == 'high']),
            'compliance_flags': len([e for e in audit_trail if e.get('compliance_flag')])
        }
    
    @staticmethod
    def _group_activities_by_action(audit_trail: List[Dict]) -> Dict:
        """Group audit activities by action type"""
        grouped = {}
        
        for entry in audit_trail:
            action = entry['action']
            if action not in grouped:
                grouped[action] = []
            grouped[action].append(entry)
        
        # Add counts
        for action in grouped:
            grouped[action] = {
                'count': len(grouped[action]),
                'activities': grouped[action]
            }
        
        return grouped
    
    @staticmethod
    def _group_activities_by_user(audit_trail: List[Dict]) -> Dict:
        """Group audit activities by user"""
        grouped = {}
        
        for entry in audit_trail:
            user_id = entry['user_id']
            if user_id not in grouped:
                grouped[user_id] = []
            grouped[user_id].append(entry)
        
        # Add counts and user info
        for user_id in grouped:
            user = User.query.get(user_id)
            grouped[user_id] = {
                'user_name': user.name if user else f'User {user_id}',
                'user_role': user.role if user else 'Unknown',
                'count': len(grouped[user_id]),
                'activities': grouped[user_id]
            }
        
        return grouped
    
    @staticmethod
    def _group_activities_by_asset(audit_trail: List[Dict]) -> Dict:
        """Group audit activities by asset"""
        grouped = {}
        
        for entry in audit_trail:
            asset_id = entry['asset_id']
            if asset_id not in grouped:
                grouped[asset_id] = []
            grouped[asset_id].append(entry)
        
        # Add counts and asset info
        for asset_id in grouped:
            asset = Asset.query.get(asset_id)
            grouped[asset_id] = {
                'asset_name': asset.name if asset else f'Asset {asset_id}',
                'asset_tag': asset.asset_tag if asset else 'N/A',
                'asset_category': asset.category if asset else 'Unknown',
                'count': len(grouped[asset_id]),
                'activities': grouped[asset_id]
            }
        
        return grouped
    
    @staticmethod
    def _identify_compliance_issues(audit_trail: List[Dict]) -> List[Dict]:
        """Identify compliance issues in audit trail"""
        issues = []
        
        for entry in audit_trail:
            if entry.get('compliance_flag'):
                issues.append({
                    'timestamp': entry['timestamp'],
                    'asset_id': entry['asset_id'],
                    'action': entry['action'],
                    'user_id': entry['user_id'],
                    'issue_type': 'compliance_flag',
                    'severity': 'high' if entry.get('impact_level') == 'high' else 'medium',
                    'details': entry['details']
                })
        
        return issues
    
    @staticmethod
    def _identify_suspicious_activities(audit_trail: List[Dict]) -> List[Dict]:
        """Identify suspicious activities"""
        suspicious = []
        
        # Look for patterns that might indicate suspicious activity
        for entry in audit_trail:
            # Activities outside business hours
            timestamp = datetime.fromisoformat(entry['timestamp'])
            if timestamp.hour < 6 or timestamp.hour > 22:
                if entry.get('impact_level') in ['high', 'medium']:
                    suspicious.append({
                        'timestamp': entry['timestamp'],
                        'asset_id': entry['asset_id'],
                        'action': entry['action'],
                        'user_id': entry['user_id'],
                        'issue_type': 'unusual_time',
                        'severity': 'medium',
                        'details': f'Activity performed at {timestamp.strftime("%H:%M")}'
                    })
        
        return suspicious
    
    @staticmethod
    def _generate_audit_recommendations(audit_report: Dict) -> List[str]:
        """Generate recommendations based on audit report"""
        recommendations = []
        
        summary = audit_report['summary']
        
        if summary['compliance_flags'] > 0:
            recommendations.append(f"Review {summary['compliance_flags']} compliance-flagged activities")
        
        if summary['high_impact_count'] > summary['total_activities'] * 0.3:
            recommendations.append("High proportion of high-impact activities - review operational procedures")
        
        if len(audit_report['suspicious_activities']) > 0:
            recommendations.append("Investigate suspicious activities identified in audit trail")
        
        # User activity recommendations
        user_groups = audit_report['activities_by_user']
        for user_id, user_data in user_groups.items():
            if user_data['count'] > 100:  # Arbitrary threshold
                recommendations.append(f"Review high activity volume for {user_data['user_name']}")
        
        return recommendations
    
    @staticmethod
    def _group_activities_by_day(audit_trail: List[Dict]) -> Dict:
        """Group activities by day"""
        grouped = {}
        
        for entry in audit_trail:
            date = datetime.fromisoformat(entry['timestamp']).date().isoformat()
            if date not in grouped:
                grouped[date] = 0
            grouped[date] += 1
        
        return grouped
    
    @staticmethod
    def _get_top_actions(audit_trail: List[Dict], limit: int = 10) -> List[Dict]:
        """Get most common actions"""
        action_counts = {}
        
        for entry in audit_trail:
            action = entry['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{'action': action, 'count': count} for action, count in sorted_actions[:limit]]
    
    @staticmethod
    def _get_most_active_users(audit_trail: List[Dict], limit: int = 10) -> List[Dict]:
        """Get most active users"""
        user_counts = {}
        
        for entry in audit_trail:
            user_id = entry['user_id']
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for user_id, count in sorted_users[:limit]:
            user = User.query.get(user_id)
            result.append({
                'user_id': user_id,
                'user_name': user.name if user else f'User {user_id}',
                'activity_count': count
            })
        
        return result
    
    @staticmethod
    def _get_most_active_assets(audit_trail: List[Dict], limit: int = 10) -> List[Dict]:
        """Get most active assets"""
        asset_counts = {}
        
        for entry in audit_trail:
            asset_id = entry['asset_id']
            asset_counts[asset_id] = asset_counts.get(asset_id, 0) + 1
        
        sorted_assets = sorted(asset_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for asset_id, count in sorted_assets[:limit]:
            asset = Asset.query.get(asset_id)
            result.append({
                'asset_id': asset_id,
                'asset_name': asset.name if asset else f'Asset {asset_id}',
                'activity_count': count
            })
        
        return result
    
    @staticmethod
    def _check_business_hours_anomalies(audit_trail: List[Dict]) -> List[Dict]:
        """Check for activities outside business hours"""
        anomalies = []
        
        for entry in audit_trail:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            if timestamp.hour < 6 or timestamp.hour > 22:
                anomalies.append({
                    'type': 'outside_business_hours',
                    'timestamp': entry['timestamp'],
                    'user_id': entry['user_id'],
                    'asset_id': entry['asset_id'],
                    'action': entry['action'],
                    'severity': 'low'
                })
        
        return anomalies
    
    @staticmethod
    def _check_rapid_activities(audit_trail: List[Dict]) -> List[Dict]:
        """Check for rapid successive activities"""
        anomalies = []
        
        # Sort by timestamp
        sorted_trail = sorted(audit_trail, key=lambda x: x['timestamp'])
        
        for i in range(1, len(sorted_trail)):
            prev_entry = sorted_trail[i-1]
            curr_entry = sorted_trail[i]
            
            prev_time = datetime.fromisoformat(prev_entry['timestamp'])
            curr_time = datetime.fromisoformat(curr_entry['timestamp'])
            
            # Check if activities are less than 1 minute apart
            if (curr_time - prev_time).total_seconds() < 60:
                if prev_entry['user_id'] == curr_entry['user_id']:
                    anomalies.append({
                        'type': 'rapid_successive_activities',
                        'timestamp': curr_entry['timestamp'],
                        'user_id': curr_entry['user_id'],
                        'asset_id': curr_entry['asset_id'],
                        'actions': [prev_entry['action'], curr_entry['action']],
                        'severity': 'medium'
                    })
        
        return anomalies
    
    @staticmethod
    def _convert_audit_to_csv(export_data: Dict) -> Dict:
        """Convert audit data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        fieldnames = [
            'timestamp', 'asset_id', 'asset_name', 'asset_tag', 'action',
            'user_id', 'impact_level', 'compliance_flag', 'details'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in export_data['audit_trail']:
            row = {
                'timestamp': entry['timestamp'],
                'asset_id': entry['asset_id'],
                'asset_name': entry.get('asset_name', ''),
                'asset_tag': entry.get('asset_tag', ''),
                'action': entry['action'],
                'user_id': entry['user_id'],
                'impact_level': entry.get('impact_level', ''),
                'compliance_flag': entry.get('compliance_flag', False),
                'details': str(entry.get('details', {}))
            }
            writer.writerow(row)
        
        return {
            'format': 'csv',
            'filename': f'audit_trail_{datetime.utcnow().strftime("%Y%m%d")}.csv',
            'content': output.getvalue()
        }
    
    @staticmethod
    def _convert_audit_to_excel(export_data: Dict) -> Dict:
        """Convert audit data to Excel format (placeholder)"""
        # This would use a library like openpyxl
        return {
            'format': 'excel',
            'filename': f'audit_trail_{datetime.utcnow().strftime("%Y%m%d")}.xlsx',
            'content': str(export_data)  # Placeholder
        }
