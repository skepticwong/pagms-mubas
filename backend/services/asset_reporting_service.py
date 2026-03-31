"""
Asset Reporting Service - Comprehensive reporting and document generation
Handles asset report generation, export, and compliance reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from io import BytesIO
import csv
from models import db, Asset, AssetMaintenance, AssetTransfer, Grant, User
from services.asset_analytics_service import AssetAnalyticsService
from services.asset_maintenance_service import AssetMaintenanceService
from services.asset_alert_service import AssetAlertService

class AssetReportingService:
    """Service for comprehensive asset reporting"""
    
    @staticmethod
    def generate_asset_inventory_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive asset inventory report"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        report = {
            'report_type': 'Asset Inventory',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_assets': len(assets),
                'total_value': sum(a.purchase_cost or 0 for a in assets),
                'active_assets': len([a for a in assets if a.status == 'ACTIVE']),
                'categories': list(set(a.category for a in assets if a.category)),
                'source_types': list(set(a.source_type for a in assets))
            },
            'assets': []
        }
        
        for asset in assets:
            asset_data = asset.to_dict()
            
            # Add additional reporting fields
            asset_data['maintenance_history_count'] = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
            asset_data['transfer_count'] = AssetTransfer.query.filter_by(asset_id=asset.id).count()
            asset_data['last_maintenance'] = None
            asset_data['next_maintenance'] = None
            
            # Get maintenance info
            last_maintenance = AssetMaintenance.query.filter_by(asset_id=asset.id).order_by(AssetMaintenance.performed_date.desc()).first()
            if last_maintenance:
                asset_data['last_maintenance'] = {
                    'date': last_maintenance.performed_date.isoformat(),
                    'type': last_maintenance.maintenance_type,
                    'cost': last_maintenance.cost
                }
            
            asset_data['next_maintenance'] = asset.next_maintenance_date.isoformat() if asset.next_maintenance_date else None
            
            report['assets'].append(asset_data)
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'inventory')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'inventory')
        else:
            return report
    
    @staticmethod
    def generate_maintenance_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive maintenance report"""
        maintenance_stats = AssetMaintenanceService.get_maintenance_statistics(grant_id)
        maintenance_history = db.session.query(AssetMaintenance).join(Asset).filter(Asset.grant_id == grant_id).order_by(AssetMaintenance.performed_date.desc()).all()
        
        report = {
            'report_type': 'Maintenance Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': maintenance_stats,
            'maintenance_records': []
        }
        
        for record in maintenance_history:
            record_data = record.to_dict()
            record_data['asset_name'] = record.asset.name
            record_data['asset_tag'] = record.asset.asset_tag
            record_data['asset_category'] = record.asset.category
            report['maintenance_records'].append(record_data)
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'maintenance')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'maintenance')
        else:
            return report
    
    @staticmethod
    def generate_compliance_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive compliance report"""
        alerts = AssetAlertService.generate_all_alerts(grant_id)
        compliance_analytics = AssetAnalyticsService._get_compliance_analytics(grant_id)
        
        report = {
            'report_type': 'Compliance Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'compliance_score': compliance_analytics['compliance_score'],
            'summary': {
                'total_alerts': len(alerts),
                'critical_alerts': compliance_analytics['critical_alerts'],
                'high_alerts': compliance_analytics['high_alerts'],
                'alert_categories': compliance_analytics['alert_categories'],
                'risk_factors': compliance_analytics['risk_factors']
            },
            'alerts': alerts,
            'recommendations': AssetReportingService._generate_compliance_recommendations(compliance_analytics)
        }
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'compliance')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'compliance')
        else:
            return report
    
    @staticmethod
    def generate_financial_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive financial report"""
        financial_analytics = AssetAnalyticsService._get_financial_analytics(grant_id)
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        report = {
            'report_type': 'Financial Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': financial_analytics,
            'asset_breakdown': []
        }
        
        for asset in assets:
            asset_data = {
                'id': asset.id,
                'name': asset.name,
                'category': asset.category,
                'source_type': asset.source_type,
                'purchase_cost': asset.purchase_cost,
                'depreciated_value': asset.depreciation_value,
                'rental_fee_total': asset.rental_fee_total,
                'maintenance_costs': 0
            }
            
            # Get maintenance costs
            maintenance_cost = db.session.query(db.func.sum(AssetMaintenance.cost)).filter_by(asset_id=asset.id).scalar() or 0
            asset_data['maintenance_costs'] = maintenance_cost
            asset_data['total_cost_of_ownership'] = (asset_data['purchase_cost'] or 0) + maintenance_cost
            
            report['asset_breakdown'].append(asset_data)
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'financial')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'financial')
        else:
            return report
    
    @staticmethod
    def generate_utilization_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive utilization report"""
        utilization_analytics = AssetAnalyticsService._get_utilization_analytics(grant_id)
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        report = {
            'report_type': 'Utilization Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': utilization_analytics,
            'asset_utilization': []
        }
        
        for asset in assets:
            asset_data = asset.to_dict()
            asset_data['transfer_count'] = AssetTransfer.query.filter_by(asset_id=asset.id).count()
            asset_data['custody_duration'] = AssetReportingService._calculate_custody_duration(asset.id)
            asset_data['utilization_score'] = AssetReportingService._calculate_utilization_score(asset)
            
            report['asset_utilization'].append(asset_data)
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'utilization')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'utilization')
        else:
            return report
    
    @staticmethod
    def generate_disposition_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive disposition report"""
        disposition_summary = AssetReportingService.get_disposition_summary(grant_id)
        pending_dispositions = AssetReportingService.get_pending_dispositions(grant_id)
        
        report = {
            'report_type': 'Disposition Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': disposition_summary,
            'pending_dispositions': pending_dispositions,
            'recommendations': AssetReportingService._generate_disposition_recommendations(disposition_summary)
        }
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'disposition')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'disposition')
        else:
            return report
    
    @staticmethod
    def generate_audit_trail_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate comprehensive audit trail report"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        report = {
            'report_type': 'Audit Trail Report',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'audit_trail': []
        }
        
        for asset in assets:
            asset_audit = {
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_tag': asset.asset_tag,
                'created_at': asset.created_at.isoformat(),
                'created_by': asset.created_by_user_id,
                'status_changes': [],
                'transfers': [],
                'maintenance_records': [],
                'disposition_info': None
            }
            
            # Get transfers
            transfers = AssetTransfer.query.filter_by(asset_id=asset.id).order_by(AssetTransfer.created_at).all()
            for transfer in transfers:
                asset_audit['transfers'].append({
                    'date': transfer.created_at.isoformat(),
                    'from_user': transfer.from_user_id,
                    'to_user': transfer.to_user_id,
                    'reason': transfer.reason,
                    'approved_by': transfer.approved_by
                })
            
            # Get maintenance records
            maintenance_records = AssetMaintenance.query.filter_by(asset_id=asset.id).order_by(AssetMaintenance.created_at).all()
            for record in maintenance_records:
                asset_audit['maintenance_records'].append({
                    'date': record.created_at.isoformat(),
                    'type': record.maintenance_type,
                    'description': record.description,
                    'cost': record.cost,
                    'performed_by': record.performed_by
                })
            
            # Disposition info
            if asset.status in ['DISPOSED', 'TRANSFERRED', 'RETURNED']:
                asset_audit['disposition_info'] = {
                    'method': asset.disposition_method,
                    'date': asset.disposition_date.isoformat() if asset.disposition_date else None,
                    'approved_by': asset.disposition_approved_by,
                    'notes': asset.disposition_notes
                }
            
            report['audit_trail'].append(asset_audit)
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'audit_trail')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'audit_trail')
        else:
            return report
    
    @staticmethod
    def generate_summary_report(grant_id: int, format_type: str = 'json') -> Dict:
        """Generate executive summary report"""
        analytics = AssetAnalyticsService.get_comprehensive_analytics(grant_id)
        
        report = {
            'report_type': 'Executive Summary',
            'grant_id': grant_id,
            'generated_at': datetime.utcnow().isoformat(),
            'executive_summary': {
                'total_assets': analytics['overview']['total_assets'],
                'total_investment': analytics['financial']['total_investment'],
                'compliance_score': analytics['compliance']['compliance_score'],
                'performance_score': analytics['performance']['overall_performance_score'],
                'critical_issues': analytics['compliance']['critical_alerts'],
                'upcoming_maintenance': len(analytics['maintenance']['upcoming_maintenance']),
                'pending_dispositions': len(analytics['forecasting']['replacement_forecast']['next_year'])
            },
            'key_insights': AssetReportingService._generate_key_insights(analytics),
            'recommendations': AssetReportingService._generate_executive_recommendations(analytics),
            'risk_assessment': AssetReportingService._generate_risk_assessment(analytics)
        }
        
        if format_type == 'csv':
            return AssetReportingService._convert_to_csv(report, 'summary')
        elif format_type == 'excel':
            return AssetReportingService._convert_to_excel(report, 'summary')
        else:
            return report
    
    @staticmethod
    def _convert_to_csv(report_data: Dict, report_type: str) -> Dict:
        """Convert report data to CSV format"""
        output = BytesIO()
        
        if report_type == 'inventory':
            fieldnames = [
                'id', 'name', 'asset_tag', 'category', 'source_type', 'status',
                'purchase_cost', 'custodian_user_id', 'created_at',
                'maintenance_history_count', 'transfer_count'
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for asset in report_data['assets']:
                row = {field: asset.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        elif report_type == 'maintenance':
            fieldnames = [
                'id', 'asset_name', 'asset_tag', 'maintenance_type', 'description',
                'performed_date', 'performed_by', 'cost', 'notes'
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in report_data['maintenance_records']:
                row = {field: record.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        # Add other report types as needed
        
        output.seek(0)
        return {
            'format': 'csv',
            'filename': f'asset_{report_type}_report_{datetime.utcnow().strftime("%Y%m%d")}.csv',
            'content': output.getvalue()
        }
    
    @staticmethod
    def _convert_to_excel(report_data: Dict, report_type: str) -> Dict:
        """Convert report data to Excel format (placeholder)"""
        # This would use a library like openpyxl or xlsxwriter
        # For now, return the JSON data
        return {
            'format': 'excel',
            'filename': f'asset_{report_type}_report_{datetime.utcnow().strftime("%Y%m%d")}.xlsx',
            'content': json.dumps(report_data, indent=2)
        }
    
    @staticmethod
    def _calculate_custody_duration(asset_id: int) -> int:
        """Calculate total days asset has been in custody"""
        transfers = AssetTransfer.query.filter_by(asset_id=asset_id).order_by(AssetTransfer.created_at).all()
        
        if not transfers:
            return 0
        
        total_days = 0
        for i, transfer in enumerate(transfers):
            start_date = transfer.created_at.date()
            if i < len(transfers) - 1:
                end_date = transfers[i + 1].created_at.date()
            else:
                end_date = datetime.utcnow().date()
            
            total_days += (end_date - start_date).days
        
        return total_days
    
    @staticmethod
    def _calculate_utilization_score(asset) -> float:
        """Calculate utilization score for an asset"""
        score = 0
        
        # Transfer frequency
        transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
        if transfer_count > 5:
            score += 25
        elif transfer_count > 2:
            score += 15
        elif transfer_count > 0:
            score += 10
        
        # Custody duration
        custody_days = AssetReportingService._calculate_custody_duration(asset.id)
        if custody_days > 365:
            score += 25
        elif custody_days > 180:
            score += 15
        elif custody_days > 30:
            score += 10
        
        # Maintenance activity
        maintenance_count = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
        if maintenance_count > 3:
            score += 25
        elif maintenance_count > 1:
            score += 15
        elif maintenance_count > 0:
            score += 10
        
        # Current status
        if asset.status == 'ACTIVE':
            score += 25
        elif asset.status in ['IN_REPAIR', 'LENDED']:
            score += 15
        
        return min(100, score)
    
    @staticmethod
    def _generate_compliance_recommendations(compliance_analytics: Dict) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if compliance_analytics['compliance_score'] < 80:
            recommendations.append("Overall compliance score requires improvement")
        
        if compliance_analytics['critical_alerts'] > 0:
            recommendations.append("Address critical compliance issues immediately")
        
        if compliance_analytics['high_alerts'] > 5:
            recommendations.append("Review and resolve high-priority alerts")
        
        for risk_factor in compliance_analytics['risk_factors']:
            recommendations.append(f"Risk factor: {risk_factor}")
        
        return recommendations
    
    @staticmethod
    def _generate_disposition_recommendations(disposition_summary: Dict) -> List[str]:
        """Generate disposition recommendations"""
        recommendations = []
        
        if disposition_summary['pending_disposition'] > 0:
            recommendations.append(f"{disposition_summary['pending_disposition']} assets require disposition")
        
        if len(disposition_summary['high_value_pending']) > 0:
            recommendations.append("High-value assets require immediate disposition planning")
        
        if disposition_summary['disposed'] == 0 and disposition_summary['total_assets'] > 0:
            recommendations.append("No assets have been disposed - consider disposition planning")
        
        return recommendations
    
    @staticmethod
    def _generate_key_insights(analytics: Dict) -> List[str]:
        """Generate key insights from analytics"""
        insights = []
        
        # Asset insights
        if analytics['overview']['total_assets'] > 50:
            insights.append("Large asset inventory requires robust management")
        
        if analytics['overview']['average_asset_age'] > 1000:
            insights.append("Asset aging requires replacement planning")
        
        # Financial insights
        if analytics['financial']['maintenance_costs'] > analytics['financial']['total_investment'] * 0.2:
            insights.append("High maintenance costs relative to asset value")
        
        # Performance insights
        if analytics['performance']['overall_performance_score'] < 70:
            insights.append("Overall asset performance requires improvement")
        
        # Compliance insights
        if analytics['compliance']['compliance_score'] < 90:
            insights.append("Compliance issues need attention")
        
        return insights
    
    @staticmethod
    def _generate_executive_recommendations(analytics: Dict) -> List[str]:
        """Generate executive-level recommendations"""
        recommendations = []
        
        # Strategic recommendations
        if analytics['forecasting']['replacement_forecast']['total_replacement_value'] > 50000:
            recommendations.append("Plan for significant asset replacement costs in next 3 years")
        
        if analytics['compliance']['critical_alerts'] > 0:
            recommendations.append("Immediate action required for critical compliance issues")
        
        if analytics['maintenance']['overdue_maintenance'] > 5:
            recommendations.append("Implement proactive maintenance scheduling")
        
        # Operational recommendations
        if len(analytics['utilization']['underutilized_assets']) > analytics['overview']['total_assets'] * 0.2:
            recommendations.append("Review asset utilization and consider redistribution")
        
        # Financial recommendations
        if analytics['financial']['roi_metrics']['maintenance_ratio'] > 0.3:
            recommendations.append("Consider asset replacement to reduce maintenance costs")
        
        return recommendations
    
    @staticmethod
    def _generate_risk_assessment(analytics: Dict) -> Dict:
        """Generate risk assessment"""
        risk_levels = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
        
        # Assess compliance risk
        if analytics['compliance']['compliance_score'] < 50:
            risk_levels['critical'] += 1
        elif analytics['compliance']['compliance_score'] < 70:
            risk_levels['high'] += 1
        elif analytics['compliance']['compliance_score'] < 85:
            risk_levels['medium'] += 1
        else:
            risk_levels['low'] += 1
        
        # Assess financial risk
        if analytics['financial']['maintenance_costs'] > analytics['financial']['total_investment'] * 0.4:
            risk_levels['high'] += 1
        elif analytics['financial']['maintenance_costs'] > analytics['financial']['total_investment'] * 0.2:
            risk_levels['medium'] += 1
        
        # Assess operational risk
        if analytics['maintenance']['overdue_maintenance'] > 10:
            risk_levels['high'] += 1
        elif analytics['maintenance']['overdue_maintenance'] > 5:
            risk_levels['medium'] += 1
        
        # Determine overall risk level
        total_risk = sum(risk_levels.values())
        if risk_levels['critical'] > 0 or total_risk > 5:
            overall_risk = 'critical'
        elif risk_levels['high'] > 1 or total_risk > 3:
            overall_risk = 'high'
        elif risk_levels['medium'] > 2 or total_risk > 1:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': risk_levels,
            'mitigation_strategies': AssetReportingService._get_mitigation_strategies(overall_risk)
        }
    
    @staticmethod
    def _get_mitigation_strategies(risk_level: str) -> List[str]:
        """Get risk mitigation strategies"""
        strategies = {
            'critical': [
                "Immediate action required for critical issues",
                "Daily monitoring of compliance status",
                "Emergency maintenance scheduling",
                "Executive oversight and reporting"
            ],
            'high': [
                "Weekly compliance reviews",
                "Accelerated maintenance scheduling",
                "Increased monitoring frequency",
                "Management intervention protocols"
            ],
            'medium': [
                "Monthly compliance reviews",
                "Preventive maintenance programs",
                "Regular performance monitoring",
                "Staff training and awareness"
            ],
            'low': [
                "Standard operating procedures",
                "Regular maintenance schedules",
                "Periodic performance reviews",
                "Continuous improvement programs"
            ]
        }
        
        return strategies.get(risk_level, strategies['medium'])
    
    # Helper methods for getting disposition data
    @staticmethod
    def get_disposition_summary(grant_id: int) -> Dict:
        """Get disposition summary (reusing existing service)"""
        from services.asset_disposition_service import AssetDispositionService
        return AssetDispositionService.get_disposition_summary(grant_id)
    
    @staticmethod
    def get_pending_dispositions(grant_id: int) -> List[Dict]:
        """Get pending dispositions (reusing existing service)"""
        from services.asset_disposition_service import AssetDispositionService
        return AssetDispositionService.get_pending_dispositions(grant_id)
