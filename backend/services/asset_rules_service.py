"""
Asset Rules Service - Asset-specific rules engine integration
Handles asset acquisition, usage, and disposition rules
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Rule, FunderProfile, Grant, Asset, User
from services.rule_service import RuleService

class AssetRulesService:
    """Service for managing asset-specific rules and compliance"""
    
    @staticmethod
    def get_default_asset_rules() -> List[Dict]:
        """Get default asset rules for new grants"""
        return [
            {
                'name': 'High-Value Procurement Threshold',
                'category': 'procurement',
                'logic_config': {
                    'field': 'purchase_cost',
                    'operator': 'greater_than',
                    'value': 5000,
                    'applies_to': 'equipment'
                },
                'outcome': 'PRIOR_APPROVAL',
                'guidance_text': 'Equipment purchases over $5,000 require prior approval from RSU',
                'priority_level': 2
            },
            {
                'name': 'Very High-Value Procurement Threshold',
                'category': 'procurement',
                'logic_config': {
                    'field': 'purchase_cost',
                    'operator': 'greater_than',
                    'value': 25000,
                    'applies_to': 'equipment'
                },
                'outcome': 'PRIOR_APPROVAL',
                'guidance_text': 'Equipment purchases over $25,000 require funder approval',
                'priority_level': 1
            },
            {
                'name': 'Unallowable Equipment Categories',
                'category': 'procurement',
                'logic_config': {
                    'field': 'category',
                    'operator': 'in_list',
                    'value': ['Luxury Vehicle', 'Entertainment', 'Personal Use', 'Jewelry']
                },
                'outcome': 'BLOCK',
                'guidance_text': 'This equipment category is not allowable under grant terms',
                'priority_level': 1
            },
            {
                'name': 'Rental vs Purchase Analysis',
                'category': 'cost_effectiveness',
                'logic_config': {
                    'field': 'rental_fee_total',
                    'operator': 'greater_than',
                    'value': 1000
                },
                'outcome': 'WARN',
                'guidance_text': 'Consider purchasing instead of renting for long-term cost savings',
                'priority_level': 3
            },
            {
                'name': 'Long-Term Rental Warning',
                'category': 'cost_effectiveness',
                'logic_config': {
                    'field': 'rental_period_days',
                    'operator': 'greater_than',
                    'value': 180
                },
                'outcome': 'WARN',
                'guidance_text': 'Rental period exceeds 6 months. Consider purchasing instead.',
                'priority_level': 3
            },
            {
                'name': 'Asset Closeout Compliance',
                'category': 'closeout',
                'logic_config': {
                    'field': 'active_assets_count',
                    'operator': 'greater_than',
                    'value': 0
                },
                'outcome': 'BLOCK',
                'guidance_text': 'Cannot close grant until all assets are properly disposed',
                'priority_level': 1
            },
            {
                'name': 'Overdue Return Alert',
                'category': 'compliance',
                'logic_config': {
                    'field': 'days_overdue',
                    'operator': 'greater_than',
                    'value': 7
                },
                'outcome': 'WARN',
                'guidance_text': 'Asset return is overdue by more than 7 days. Immediate action required.',
                'priority_level': 2
            },
            {
                'name': 'Maintenance Schedule Compliance',
                'category': 'maintenance',
                'logic_config': {
                    'field': 'days_since_maintenance',
                    'operator': 'greater_than',
                    'value': 365
                },
                'outcome': 'WARN',
                'guidance_text': 'Asset requires annual maintenance inspection',
                'priority_level': 3
            }
        ]
    
    @staticmethod
    def create_asset_rules_for_grant(grant_id: int):
        """Create default asset rules for a new grant"""
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")
        
        # Get or create funder profile for the grant
        funder_profile = FunderProfile.query.filter_by(grant_id=grant_id).first()
        if not funder_profile:
            funder_profile = FunderProfile(
                name=f"{grant.grant_code} Asset Rules",
                grant_id=grant_id,
                is_active=True
            )
            db.session.add(funder_profile)
            db.session.flush()
        
        # Add default asset rules
        default_rules = AssetRulesService.get_default_asset_rules()
        
        for rule_data in default_rules:
            existing_rule = Rule.query.filter_by(
                funder_profile_id=funder_profile.id,
                name=rule_data['name']
            ).first()
            
            if not existing_rule:
                rule = Rule(
                    funder_profile_id=funder_profile.id,
                    name=rule_data['name'],
                    category=rule_data['category'],
                    logic_config=rule_data['logic_config'],
                    outcome=rule_data['outcome'],
                    guidance_text=rule_data['guidance_text'],
                    priority_level=rule_data['priority_level'],
                    is_active=True
                )
                db.session.add(rule)
        
        db.session.commit()
        return funder_profile
    
    @staticmethod
    def evaluate_asset_request(asset_data: Dict, grant_id: int, user_id: int) -> Dict:
        """Evaluate asset request against rules"""
        try:
            # Ensure asset rules exist for the grant
            AssetRulesService.create_asset_rules_for_grant(grant_id)
            
            # Prepare context for rule evaluation
            context = {
                'category': asset_data.get('category', 'Equipment'),
                'source_type': asset_data.get('source_type'),
                'cost': asset_data.get('estimated_cost', 0),
                'rental_fee': asset_data.get('rental_fee', 0),
                'grant_id': grant_id,
                'user_id': user_id
            }
            
            # Calculate rental period if return date is provided
            if asset_data.get('return_date') and asset_data.get('source_type') == 'LENDED':
                start_date = datetime.utcnow().date()
                end_date = datetime.strptime(asset_data['return_date'], '%Y-%m-%d').date()
                context['rental_period_days'] = (end_date - start_date).days
            
            # Evaluate using existing rule service
            result = RuleService.evaluate_action('ASSET_ACQUISITION', context, grant_id)
            
            # Add asset-specific recommendations
            if result['outcome'] == 'PASS':
                recommendations = AssetRulesService._get_cost_recommendations(asset_data)
                if recommendations:
                    result['recommendations'] = recommendations
            
            return result
            
        except Exception as e:
            return {
                'outcome': 'ERROR',
                'error': str(e),
                'triggered_rules': []
            }
    
    @staticmethod
    def check_asset_compliance(asset_id: int) -> Dict:
        """Check asset compliance with rules"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        compliance_issues = []
        
        # Check overdue returns
        if asset.source_type == 'LENDED' and asset.expected_return_date:
            days_overdue = (datetime.utcnow().date() - asset.expected_return_date).days
            if days_overdue > 0:
                compliance_issues.append({
                    'type': 'overdue_return',
                    'severity': 'high' if days_overdue > 7 else 'medium',
                    'message': f'Asset is {days_overdue} days overdue for return',
                    'action_required': 'Return asset to lender immediately'
                })
        
        # Check maintenance compliance
        if asset.last_maintenance_date:
            days_since_maintenance = (datetime.utcnow().date() - asset.last_maintenance_date).days
            if days_since_maintenance > 365:
                compliance_issues.append({
                    'type': 'maintenance_overdue',
                    'severity': 'medium',
                    'message': f'Asset is {days_since_maintenance} days since last maintenance',
                    'action_required': 'Schedule maintenance inspection'
                })
        
        # Check upcoming maintenance
        if asset.next_maintenance_date:
            days_until_maintenance = (asset.next_maintenance_date - datetime.utcnow().date()).days
            if days_until_maintenance <= 30 and days_until_maintenance >= 0:
                compliance_issues.append({
                    'type': 'maintenance_due',
                    'severity': 'low',
                    'message': f'Maintenance due in {days_until_maintenance} days',
                    'action_required': 'Schedule maintenance appointment'
                })
        
        return {
            'compliant': len(compliance_issues) == 0,
            'issues': compliance_issues,
            'asset': asset.to_dict()
        }
    
    @staticmethod
    def check_grant_closeout_compliance(grant_id: int) -> Dict:
        """Check if grant can be closed based on asset compliance"""
        active_assets = Asset.query.filter(
            Asset.grant_id == grant_id,
            Asset.status.in_(['ACTIVE', 'IN_REPAIR', 'LENDED'])
        ).all()
        
        compliance_issues = []
        
        for asset in active_assets:
            asset_compliance = AssetRulesService.check_asset_compliance(asset.id)
            if not asset_compliance['compliant']:
                compliance_issues.extend(asset_compliance['issues'])
        
        # Check for any assets that need disposition
        if active_assets:
            compliance_issues.append({
                'type': 'assets_need_disposition',
                'severity': 'high',
                'message': f'{len(active_assets)} assets need disposition before closeout',
                'action_required': 'Dispose or transfer all assets',
                'assets': [asset.to_dict() for asset in active_assets]
            })
        
        return {
            'can_close': len(compliance_issues) == 0,
            'issues': compliance_issues,
            'total_assets': len(active_assets)
        }
    
    @staticmethod
    def get_asset_recommendations(asset_id: int) -> List[Dict]:
        """Get recommendations for asset management"""
        asset = Asset.query.get(asset_id)
        if not asset:
            return []
        
        recommendations = []
        
        # Cost optimization recommendations
        if asset.source_type == 'LENDED' and asset.rental_fee_total > 1000:
            recommendations.append({
                'type': 'cost_optimization',
                'title': 'Consider Purchase Option',
                'description': f'Rental cost of ${asset.rental_fee_total} may exceed purchase cost over time',
                'priority': 'medium'
            })
        
        # Maintenance recommendations
        if not asset.next_maintenance_date and asset.status == 'ACTIVE':
            recommendations.append({
                'type': 'maintenance',
                'title': 'Schedule Maintenance',
                'description': 'Set up regular maintenance schedule for this asset',
                'priority': 'low'
            })
        
        # Disposition recommendations
        if asset.status == 'ACTIVE' and asset.purchase_cost > 10000:
            recommendations.append({
                'type': 'disposition',
                'title': 'Plan for Disposition',
                'description': 'High-value asset requires disposition planning',
                'priority': 'medium'
            })
        
        return recommendations
    
    @staticmethod
    def _get_cost_recommendations(asset_data: Dict) -> List[str]:
        """Get cost-related recommendations for asset requests"""
        recommendations = []
        
        # Rental vs purchase analysis
        if asset_data.get('source_type') == 'LENDED':
            rental_fee = asset_data.get('rental_fee', 0)
            estimated_cost = asset_data.get('estimated_cost', 0)
            
            if rental_fee > estimated_cost * 0.3:
                recommendations.append("Rental cost exceeds 30% of estimated purchase price")
            
            if asset_data.get('return_date'):
                start_date = datetime.utcnow().date()
                end_date = datetime.strptime(asset_data['return_date'], '%Y-%m-%d').date()
                rental_days = (end_date - start_date).days
                
                if rental_days > 180:
                    recommendations.append("Consider purchasing for rentals over 6 months")
        
        # Category-specific recommendations
        category = asset_data.get('category', '').lower()
        if 'vehicle' in category:
            recommendations.append("Ensure proper insurance coverage for vehicle")
        elif 'it' in category or 'computer' in category:
            recommendations.append("Consider software licensing and security requirements")
        elif 'lab' in category:
            recommendations.append("Ensure calibration and certification requirements")
        
        return recommendations

class AssetComplianceMonitor:
    """Monitor asset compliance and generate alerts"""
    
    @staticmethod
    def get_compliance_alerts(grant_id: int = None) -> List[Dict]:
        """Get all compliance alerts for assets"""
        alerts = []
        
        # Query assets based on grant_id filter
        query = Asset.query
        if grant_id:
            query = query.filter_by(grant_id=grant_id)
        
        assets = query.all()
        
        for asset in assets:
            compliance = AssetRulesService.check_asset_compliance(asset.id)
            
            for issue in compliance['issues']:
                alerts.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'asset_tag': asset.asset_tag,
                    'grant_id': asset.grant_id,
                    'issue_type': issue['type'],
                    'severity': issue['severity'],
                    'message': issue['message'],
                    'action_required': issue['action_required'],
                    'created_at': datetime.utcnow()
                })
        
        # Sort by severity and date
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['created_at']), reverse=True)
        
        return alerts
    
    @staticmethod
    def generate_compliance_report(grant_id: int) -> Dict:
        """Generate comprehensive compliance report for a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        report = {
            'grant_id': grant_id,
            'total_assets': len(assets),
            'compliant_assets': 0,
            'non_compliant_assets': 0,
            'alerts_by_severity': {'high': 0, 'medium': 0, 'low': 0},
            'issues_by_type': {},
            'recommendations': []
        }
        
        for asset in assets:
            compliance = AssetRulesService.check_asset_compliance(asset.id)
            
            if compliance['compliant']:
                report['compliant_assets'] += 1
            else:
                report['non_compliant_assets'] += 1
                
                for issue in compliance['issues']:
                    # Count by severity
                    severity = issue['severity']
                    if severity in report['alerts_by_severity']:
                        report['alerts_by_severity'][severity] += 1
                    
                    # Count by type
                    issue_type = issue['type']
                    if issue_type not in report['issues_by_type']:
                        report['issues_by_type'][issue_type] = 0
                    report['issues_by_type'][issue_type] += 1
        
        # Add recommendations
        if report['non_compliant_assets'] > 0:
            report['recommendations'].append("Address all compliance issues before grant closeout")
        
        if report['alerts_by_severity']['high'] > 0:
            report['recommendations'].append("Immediate action required for high-priority issues")
        
        return report
