"""
Asset Analytics Service - Advanced analytics and insights
Provides comprehensive asset analytics, performance metrics, and forecasting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_
from models import db, Asset, AssetMaintenance, AssetTransfer, Grant, User
from services.asset_maintenance_service import AssetMaintenanceService
from services.asset_alert_service import AssetAlertService

class AssetAnalyticsService:
    """Service for advanced asset analytics and insights"""
    
    @staticmethod
    def get_comprehensive_analytics(grant_id: int) -> Dict:
        """Get comprehensive analytics for a grant"""
        analytics = {
            'overview': AssetAnalyticsService._get_overview_metrics(grant_id),
            'financial': AssetAnalyticsService._get_financial_analytics(grant_id),
            'utilization': AssetAnalyticsService._get_utilization_analytics(grant_id),
            'maintenance': AssetAnalyticsService._get_maintenance_analytics(grant_id),
            'compliance': AssetAnalyticsService._get_compliance_analytics(grant_id),
            'performance': AssetAnalyticsService._get_performance_analytics(grant_id),
            'forecasting': AssetAnalyticsService._get_forecasting_analytics(grant_id)
        }
        
        return analytics
    
    @staticmethod
    def _get_overview_metrics(grant_id: int) -> Dict:
        """Get overview metrics for assets"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        overview = {
            'total_assets': len(assets),
            'active_assets': len([a for a in assets if a.status == 'ACTIVE']),
            'total_value': sum(a.purchase_cost or 0 for a in assets),
            'average_asset_age': 0,
            'asset_categories': {},
            'source_types': {},
            'status_distribution': {}
        }
        
        # Calculate asset age and categories
        today = datetime.utcnow().date()
        total_age_days = 0
        assets_with_age = 0
        
        for asset in assets:
            # Categories
            category = asset.category or 'Other'
            overview['asset_categories'][category] = overview['asset_categories'].get(category, 0) + 1
            
            # Source types
            source = asset.source_type
            overview['source_types'][source] = overview['source_types'].get(source, 0) + 1
            
            # Status distribution
            status = asset.status
            overview['status_distribution'][status] = overview['status_distribution'].get(status, 0) + 1
            
            # Asset age
            if asset.acquisition_date:
                age_days = (today - asset.acquisition_date).days
                total_age_days += age_days
                assets_with_age += 1
        
        if assets_with_age > 0:
            overview['average_asset_age'] = total_age_days / assets_with_age
        
        return overview
    
    @staticmethod
    def _get_financial_analytics(grant_id: int) -> Dict:
        """Get financial analytics for assets"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        financial = {
            'total_investment': sum(a.purchase_cost or 0 for a in assets),
            'depreciated_value': sum(a.depreciation_value or 0 for a in assets),
            'maintenance_costs': 0,
            'rental_costs': sum(a.rental_fee_total or 0 for a in assets),
            'cost_per_category': {},
            'roi_metrics': {},
            'budget_utilization': 0
        }
        
        # Get maintenance costs
        maintenance_costs = db.session.query(func.sum(AssetMaintenance.cost)).join(Asset).filter(Asset.grant_id == grant_id).scalar() or 0
        financial['maintenance_costs'] = maintenance_costs
        
        # Cost per category
        for asset in assets:
            category = asset.category or 'Other'
            cost = asset.purchase_cost or 0
            financial['cost_per_category'][category] = financial['cost_per_category'].get(category, 0) + cost
        
        # ROI metrics (simplified)
        if financial['total_investment'] > 0:
            financial['roi_metrics'] = {
                'maintenance_ratio': financial['maintenance_costs'] / financial['total_investment'],
                'rental_ratio': financial['rental_costs'] / financial['total_investment'],
                'total_cost_ratio': (financial['total_investment'] + financial['maintenance_costs']) / financial['total_investment']
            }
        
        # Budget utilization (would need grant budget data)
        grant = Grant.query.get(grant_id)
        if grant and hasattr(grant, 'total_budget'):
            financial['budget_utilization'] = financial['total_investment'] / grant.total_budget
        
        return financial
    
    @staticmethod
    def _get_utilization_analytics(grant_id: int) -> Dict:
        """Get utilization analytics for assets"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        utilization = {
            'custodian_utilization': {},
            'task_utilization': {},
            'transfer_frequency': {},
            'average_utilization_rate': 0,
            'underutilized_assets': [],
            'highly_utilized_assets': []
        }
        
        # Custodian utilization
        for asset in assets:
            if asset.custodian_user_id:
                custodian_id = asset.custodian_user_id
                utilization['custodian_utilization'][custodian_id] = utilization['custodian_utilization'].get(custodian_id, 0) + 1
            
            if asset.assigned_task_id:
                task_id = asset.assigned_task_id
                utilization['task_utilization'][task_id] = utilization['task_utilization'].get(task_id, 0) + 1
        
        # Transfer frequency
        for asset in assets:
            transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
            if transfer_count > 0:
                utilization['transfer_frequency'][asset.id] = transfer_count
        
        # Calculate utilization metrics
        total_transfers = sum(utilization['transfer_frequency'].values())
        if len(assets) > 0:
            utilization['average_utilization_rate'] = total_transfers / len(assets)
        
        # Identify underutilized and highly utilized assets
        for asset in assets:
            transfer_count = utilization['transfer_frequency'].get(asset.id, 0)
            if transfer_count == 0 and asset.status == 'ACTIVE':
                utilization['underutilized_assets'].append({
                    'id': asset.id,
                    'name': asset.name,
                    'status': asset.status
                })
            elif transfer_count > 5:
                utilization['highly_utilized_assets'].append({
                    'id': asset.id,
                    'name': asset.name,
                    'transfer_count': transfer_count
                })
        
        return utilization
    
    @staticmethod
    def _get_maintenance_analytics(grant_id: int) -> Dict:
        """Get maintenance analytics"""
        maintenance_stats = AssetMaintenanceService.get_maintenance_statistics(grant_id)
        
        # Enhanced maintenance analytics
        maintenance = {
            **maintenance_stats,
            'cost_trends': AssetAnalyticsService._get_maintenance_cost_trends(grant_id),
            'category_performance': AssetAnalyticsService._get_maintenance_by_category(grant_id),
            'predictive_maintenance': AssetAnalyticsService._get_predictive_maintenance(grant_id),
            'maintenance_efficiency': AssetAnalyticsService._calculate_maintenance_efficiency(grant_id)
        }
        
        return maintenance
    
    @staticmethod
    def _get_compliance_analytics(grant_id: int) -> Dict:
        """Get compliance analytics"""
        alerts = AssetAlertService.generate_all_alerts(grant_id)
        
        compliance = {
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['severity'] == 'critical']),
            'high_alerts': len([a for a in alerts if a['severity'] == 'high']),
            'alert_categories': {},
            'compliance_score': 0,
            'risk_factors': [],
            'trending_issues': []
        }
        
        # Alert categories
        for alert in alerts:
            category = alert['category']
            compliance['alert_categories'][category] = compliance['alert_categories'].get(category, 0) + 1
        
        # Calculate compliance score
        total_assets = Asset.query.filter_by(grant_id=grant_id).count()
        if total_assets > 0:
            compliant_assets = total_assets - compliance['critical_alerts'] - compliance['high_alerts']
            compliance['compliance_score'] = (compliant_assets / total_assets) * 100
        
        # Identify risk factors
        if compliance['critical_alerts'] > 0:
            compliance['risk_factors'].append('Critical compliance issues require immediate attention')
        
        if compliance['high_alerts'] > 5:
            compliance['risk_factors'].append('High number of compliance alerts')
        
        return compliance
    
    @staticmethod
    def _get_performance_analytics(grant_id: int) -> Dict:
        """Get performance analytics"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        performance = {
            'asset_performance_scores': {},
            'category_performance': {},
            'source_type_performance': {},
            'overall_performance_score': 0,
            'top_performers': [],
            'underperformers': []
        }
        
        # Calculate performance scores for each asset
        for asset in assets:
            score = AssetAnalyticsService._calculate_asset_performance_score(asset)
            performance['asset_performance_scores'][asset.id] = score
            
            # Category performance
            category = asset.category or 'Other'
            if category not in performance['category_performance']:
                performance['category_performance'][category] = []
            performance['category_performance'][category].append(score)
            
            # Source type performance
            source = asset.source_type
            if source not in performance['source_type_performance']:
                performance['source_type_performance'][source] = []
            performance['source_type_performance'][source].append(score)
        
        # Calculate average scores
        all_scores = list(performance['asset_performance_scores'].values())
        if all_scores:
            performance['overall_performance_score'] = sum(all_scores) / len(all_scores)
        
        # Calculate category averages
        for category in performance['category_performance']:
            scores = performance['category_performance'][category]
            performance['category_performance'][category] = sum(scores) / len(scores)
        
        # Calculate source type averages
        for source in performance['source_type_performance']:
            scores = performance['source_type_performance'][source]
            performance['source_type_performance'][source] = sum(scores) / len(scores)
        
        # Identify top performers and underperformers
        sorted_assets = sorted(performance['asset_performance_scores'].items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_assets) > 0:
            # Top 20% performers
            top_count = max(1, len(sorted_assets) // 5)
            performance['top_performers'] = sorted_assets[:top_count]
            
            # Bottom 20% performers
            bottom_count = max(1, len(sorted_assets) // 5)
            performance['underperformers'] = sorted_assets[-bottom_count:]
        
        return performance
    
    @staticmethod
    def _get_forecasting_analytics(grant_id: int) -> Dict:
        """Get forecasting analytics"""
        forecasting = {
            'maintenance_forecast': AssetAnalyticsService._forecast_maintenance_needs(grant_id),
            'cost_forecast': AssetAnalyticsService._forecast_future_costs(grant_id),
            'utilization_forecast': AssetAnalyticsService._forecast_utilization_trends(grant_id),
            'replacement_forecast': AssetAnalyticsService._forecast_asset_replacements(grant_id),
            'budget_forecast': AssetAnalyticsService._forecast_budget_needs(grant_id)
        }
        
        return forecasting
    
    @staticmethod
    def _calculate_asset_performance_score(asset: Asset) -> float:
        """Calculate performance score for an individual asset (0-100)"""
        score = 50.0  # Base score
        
        # Age factor (newer is better)
        if asset.acquisition_date:
            days_old = (datetime.utcnow().date() - asset.acquisition_date).days
            if days_old < 365:
                score += 20
            elif days_old < 1095:  # 3 years
                score += 10
            elif days_old > 1825:  # 5 years
                score -= 10
        
        # Maintenance factor (well-maintained is better)
        maintenance_count = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
        if maintenance_count > 0:
            last_maintenance = AssetMaintenance.query.filter_by(asset_id=asset.id).order_by(AssetMaintenance.performed_date.desc()).first()
            if last_maintenance and last_maintenance.performed_date:
                days_since_maintenance = (datetime.utcnow().date() - last_maintenance.performed_date).days
                if days_since_maintenance < 90:
                    score += 15
                elif days_since_maintenance > 365:
                    score -= 15
        
        # Utilization factor (used assets are better)
        transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
        if transfer_count > 3:
            score += 10
        elif transfer_count == 0 and asset.status == 'ACTIVE':
            score -= 10
        
        # Compliance factor (no alerts is better)
        alerts = AssetAlertService.generate_all_alerts(asset.grant_id)
        asset_alerts = [a for a in alerts if a['asset_id'] == asset.id]
        if len(asset_alerts) == 0:
            score += 15
        elif len(asset_alerts) > 2:
            score -= 15
        
        # Value factor (higher value assets get slight bonus for importance)
        if asset.purchase_cost and asset.purchase_cost > 10000:
            score += 5
        
        # Ensure score is within 0-100 range
        return max(0, min(100, score))
    
    @staticmethod
    def _get_maintenance_cost_trends(grant_id: int) -> Dict:
        """Get maintenance cost trends over time"""
        # Get last 12 months of maintenance costs
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365)
        
        maintenance_costs = db.session.query(
            AssetMaintenance.performed_date,
            func.sum(AssetMaintenance.cost).label('total_cost'),
            func.count(AssetMaintenance.id).label('count')
        ).join(Asset).filter(
            Asset.grant_id == grant_id,
            AssetMaintenance.performed_date >= start_date
        ).group_by(
            func.strftime('%Y-%m', AssetMaintenance.performed_date)
        ).order_by(AssetMaintenance.performed_date).all()
        
        trends = {
            'period': '12 months',
            'monthly_costs': {},
            'monthly_counts': {},
            'total_cost': 0,
            'average_monthly_cost': 0
        }
        
        for record in maintenance_costs:
            month = record.performed_date.strftime('%Y-%m')
            trends['monthly_costs'][month] = float(record.total_cost)
            trends['monthly_counts'][month] = record.count
            trends['total_cost'] += float(record.total_cost)
        
        if trends['monthly_costs']:
            trends['average_monthly_cost'] = trends['total_cost'] / len(trends['monthly_costs'])
        
        return trends
    
    @staticmethod
    def _get_maintenance_by_category(grant_id: int) -> Dict:
        """Get maintenance performance by asset category"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        category_performance = {}
        
        for asset in assets:
            category = asset.category or 'Other'
            if category not in category_performance:
                category_performance[category] = {
                    'asset_count': 0,
                    'total_maintenance_cost': 0,
                    'maintenance_count': 0,
                    'average_cost_per_maintenance': 0,
                    'cost_per_asset': 0
                }
            
            category_performance[category]['asset_count'] += 1
            
            # Get maintenance costs for this asset
            maintenance_costs = db.session.query(func.sum(AssetMaintenance.cost)).filter_by(asset_id=asset.id).scalar() or 0
            maintenance_count = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
            
            category_performance[category]['total_maintenance_cost'] += maintenance_costs
            category_performance[category]['maintenance_count'] += maintenance_count
        
        # Calculate averages
        for category, data in category_performance.items():
            if data['maintenance_count'] > 0:
                data['average_cost_per_maintenance'] = data['total_maintenance_cost'] / data['maintenance_count']
            
            if data['asset_count'] > 0:
                data['cost_per_asset'] = data['total_maintenance_cost'] / data['asset_count']
        
        return category_performance
    
    @staticmethod
    def _get_predictive_maintenance(grant_id: int) -> Dict:
        """Get predictive maintenance recommendations"""
        assets = Asset.query.filter_by(grant_id=grant_id, status='ACTIVE').all()
        
        predictions = {
            'high_priority_assets': [],
            'upcoming_maintenance': [],
            'risk_assessment': {}
        }
        
        for asset in assets:
            # Calculate maintenance risk score
            risk_score = 0
            
            # Age factor
            if asset.acquisition_date:
                days_old = (datetime.utcnow().date() - asset.acquisition_date).days
                if days_old > 1825:  # 5 years
                    risk_score += 30
                elif days_old > 1095:  # 3 years
                    risk_score += 20
                elif days_old > 730:  # 2 years
                    risk_score += 10
            
            # Last maintenance factor
            if asset.last_maintenance_date:
                days_since_maintenance = (datetime.utcnow().date() - asset.last_maintenance_date).days
                if days_since_maintenance > 365:
                    risk_score += 25
                elif days_since_maintenance > 180:
                    risk_score += 15
                elif days_since_maintenance > 90:
                    risk_score += 5
            else:
                risk_score += 40  # No maintenance record
            
            # Usage factor (transfers)
            transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
            if transfer_count > 10:
                risk_score += 15
            elif transfer_count > 5:
                risk_score += 10
            
            predictions['risk_assessment'][asset.id] = {
                'asset_name': asset.name,
                'risk_score': risk_score,
                'risk_level': 'high' if risk_score > 60 else 'medium' if risk_score > 30 else 'low'
            }
            
            # Categorize assets
            if risk_score > 60:
                predictions['high_priority_assets'].append({
                    'id': asset.id,
                    'name': asset.name,
                    'risk_score': risk_score
                })
            
            if asset.next_maintenance_date:
                days_until = (asset.next_maintenance_date - datetime.utcnow().date()).days
                if days_until <= 30:
                    predictions['upcoming_maintenance'].append({
                        'id': asset.id,
                        'name': asset.name,
                        'days_until': days_until
                    })
        
        return predictions
    
    @staticmethod
    def _calculate_maintenance_efficiency(grant_id: int) -> Dict:
        """Calculate maintenance efficiency metrics"""
        efficiency = {
            'preventive_vs_corrective': {},
            'cost_efficiency': 0,
            'time_efficiency': 0,
            'downtime_reduction': 0
        }
        
        # Get maintenance records
        maintenance_records = db.session.query(AssetMaintenance).join(Asset).filter(Asset.grant_id == grant_id).all()
        
        preventive_count = len([m for m in maintenance_records if m.maintenance_type == 'Scheduled'])
        corrective_count = len([m for m in maintenance_records if m.maintenance_type == 'Repair'])
        
        total_count = preventive_count + corrective_count
        if total_count > 0:
            efficiency['preventive_vs_corrective'] = {
                'preventive': preventive_count,
                'corrective': corrective_count,
                'preventive_ratio': preventive_count / total_count
            }
        
        # Calculate cost efficiency (simplified)
        preventive_costs = sum(m.cost or 0 for m in maintenance_records if m.maintenance_type == 'Scheduled')
        corrective_costs = sum(m.cost or 0 for m in maintenance_records if m.maintenance_type == 'Repair')
        
        if corrective_costs > 0:
            efficiency['cost_efficiency'] = preventive_costs / (preventive_costs + corrective_costs)
        
        return efficiency
    
    @staticmethod
    def _forecast_maintenance_needs(grant_id: int) -> Dict:
        """Forecast future maintenance needs"""
        assets = Asset.query.filter_by(grant_id=grant_id, status='ACTIVE').all()
        
        forecast = {
            'next_quarter': [],
            'next_year': [],
            'estimated_costs': {
                'next_quarter': 0,
                'next_year': 0
            },
            'high_priority_count': 0
        }
        
        today = datetime.utcnow().date()
        next_quarter_end = today + timedelta(days=90)
        next_year_end = today + timedelta(days=365)
        
        for asset in assets:
            if asset.next_maintenance_date:
                if asset.next_maintenance_date <= next_quarter_end:
                    forecast['next_quarter'].append({
                        'id': asset.id,
                        'name': asset.name,
                        'due_date': asset.next_maintenance_date.isoformat()
                    })
                    forecast['estimated_costs']['next_quarter'] += 100  # Estimated average cost
                
                if asset.next_maintenance_date <= next_year_end:
                    forecast['next_year'].append({
                        'id': asset.id,
                        'name': asset.name,
                        'due_date': asset.next_maintenance_date.isoformat()
                    })
                    forecast['estimated_costs']['next_year'] += 100
        
        return forecast
    
    @staticmethod
    def _forecast_future_costs(grant_id: int) -> Dict:
        """Forecast future asset-related costs"""
        assets = Asset.query.filter_by(grant_id=grant_id, status='ACTIVE').all()
        
        forecast = {
            'maintenance_costs': {
                'next_6_months': 0,
                'next_year': 0
            },
            'replacement_costs': {
                'next_year': 0,
                'next_3_years': 0
            },
            'total_projected_costs': 0
        }
        
        # Simplified forecasting based on historical patterns
        for asset in assets:
            # Maintenance cost projection
            avg_maintenance_cost = 150  # Simplified average
            forecast['maintenance_costs']['next_6_months'] += avg_maintenance_cost
            forecast['maintenance_costs']['next_year'] += avg_maintenance_cost * 2
            
            # Replacement cost projection (very simplified)
            if asset.acquisition_date:
                asset_age = (datetime.utcnow().date() - asset.acquisition_date).days
                if asset_age > 1825:  # 5 years old
                    forecast['replacement_costs']['next_3_years'] += asset.purchase_cost or 0
        
        forecast['total_projected_costs'] = (
            forecast['maintenance_costs']['next_year'] +
            forecast['replacement_costs']['next_3_years']
        )
        
        return forecast
    
    @staticmethod
    def _forecast_utilization_trends(grant_id: int) -> Dict:
        """Forecast utilization trends"""
        # This would require historical utilization data
        # For now, return a simplified forecast
        return {
            'trend': 'stable',
            'projected_utilization': 75,
            'confidence_level': 0.7,
            'factors': ['Historical patterns', 'Seasonal variations']
        }
    
    @staticmethod
    def _forecast_asset_replacements(grant_id: int) -> Dict:
        """Forecast asset replacement needs"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        forecast = {
            'next_year': [],
            'next_3_years': [],
            'total_replacement_value': 0
        }
        
        today = datetime.utcnow().date()
        
        for asset in assets:
            if asset.acquisition_date:
                asset_age = (today - asset.acquisition_date).days
                
                # Simple replacement forecasting based on asset type and age
                replacement_age = 1825  # 5 years default
                
                if 'Vehicle' in (asset.category or ''):
                    replacement_age = 1095  # 3 years for vehicles
                elif 'IT' in (asset.category or ''):
                    replacement_age = 730  # 2 years for IT equipment
                
                replacement_date = asset.acquisition_date + timedelta(days=replacement_age)
                
                if replacement_date <= today + timedelta(days=365):
                    forecast['next_year'].append({
                        'id': asset.id,
                        'name': asset.name,
                        'replacement_date': replacement_date.isoformat(),
                        'estimated_cost': asset.purchase_cost or 0
                    })
                    forecast['total_replacement_value'] += asset.purchase_cost or 0
                
                elif replacement_date <= today + timedelta(days=1095):
                    forecast['next_3_years'].append({
                        'id': asset.id,
                        'name': asset.name,
                        'replacement_date': replacement_date.isoformat(),
                        'estimated_cost': asset.purchase_cost or 0
                    })
        
        return forecast
    
    @staticmethod
    def _forecast_budget_needs(grant_id: int) -> Dict:
        """Forecast future budget needs for assets"""
        maintenance_forecast = AssetAnalyticsService._forecast_maintenance_needs(grant_id)
        cost_forecast = AssetAnalyticsService._forecast_future_costs(grant_id)
        replacement_forecast = AssetAnalyticsService._forecast_asset_replacements(grant_id)
        
        forecast = {
            'next_quarter': maintenance_forecast['estimated_costs']['next_quarter'],
            'next_year': (
                cost_forecast['maintenance_costs']['next_year'] +
                replacement_forecast['total_replacement_value']
            ),
            'next_3_years': replacement_forecast['total_replacement_value'],
            'recommendations': []
        }
        
        # Generate recommendations
        if forecast['next_year'] > 10000:
            forecast['recommendations'].append('Consider budget allocation for asset replacements')
        
        if forecast['next_quarter'] > 5000:
            forecast['recommendations'].append('Plan for increased maintenance costs')
        
        return forecast
