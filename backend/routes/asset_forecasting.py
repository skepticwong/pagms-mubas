"""
Asset Forecasting Routes - Advanced forecasting and prediction endpoints
"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_analytics_service import AssetAnalyticsService
from services.asset_maintenance_service import AssetMaintenanceService
from services.asset_alert_service import AssetAlertService
from models import Asset, Grant
from typing import Dict, List

forecasting_bp = Blueprint('asset_forecasting', __name__)

@forecasting_bp.route('/assets/forecast/maintenance/<int:grant_id>', methods=['GET'])
@token_required
def forecast_maintenance(user, grant_id):
    """Get maintenance forecasting"""
    try:
        forecast = AssetAnalyticsService._forecast_maintenance_needs(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast maintenance'}), 500

@forecasting_bp.route('/assets/forecast/costs/<int:grant_id>', methods=['GET'])
@token_required
def forecast_costs(user, grant_id):
    """Get cost forecasting"""
    try:
        forecast = AssetAnalyticsService._forecast_future_costs(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast costs'}), 500

@forecasting_bp.route('/assets/forecast/replacements/<int:grant_id>', methods=['GET'])
@token_required
def forecast_replacements(user, grant_id):
    """Get asset replacement forecasting"""
    try:
        forecast = AssetAnalyticsService._forecast_asset_replacements(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast replacements'}), 500

@forecasting_bp.route('/assets/forecast/budget/<int:grant_id>', methods=['GET'])
@token_required
def forecast_budget(user, grant_id):
    """Get budget forecasting"""
    try:
        forecast = AssetAnalyticsService._forecast_budget_needs(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast budget'}), 500

@forecasting_bp.route('/assets/forecast/utilization/<int:grant_id>', methods=['GET'])
@token_required
def forecast_utilization(user, grant_id):
    """Get utilization forecasting"""
    try:
        forecast = AssetAnalyticsService._forecast_utilization_trends(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast utilization'}), 500

@forecasting_bp.route('/assets/forecast/comprehensive/<int:grant_id>', methods=['GET'])
@token_required
def get_comprehensive_forecast(user, grant_id):
    """Get comprehensive forecasting for all areas"""
    try:
        forecasting = AssetAnalyticsService._get_forecasting_analytics(grant_id)
        return jsonify(forecasting), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate comprehensive forecast'}), 500

@forecasting_bp.route('/assets/forecast/predictive-maintenance/<int:grant_id>', methods=['GET'])
@token_required
def get_predictive_maintenance(user, grant_id):
    """Get predictive maintenance recommendations"""
    try:
        predictions = AssetAnalyticsService._get_predictive_maintenance(grant_id)
        return jsonify(predictions), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get predictive maintenance'}), 500

@forecasting_bp.route('/assets/forecast/asset-lifecycle/<int:asset_id>', methods=['GET'])
@token_required
def forecast_asset_lifecycle(user, asset_id):
    """Get lifecycle prediction for specific asset"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        lifecycle_prediction = AssetForecastingService._predict_asset_lifecycle(asset)
        return jsonify(lifecycle_prediction), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to predict asset lifecycle'}), 500

@forecasting_bp.route('/assets/forecast/failure-risk/<int:grant_id>', methods=['GET'])
@token_required
def get_failure_risk_assessment(user, grant_id):
    """Get failure risk assessment for assets"""
    try:
        risk_assessment = AssetForecastingService._assess_failure_risk(grant_id)
        return jsonify(risk_assessment), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to assess failure risk'}), 500

@forecasting_bp.route('/assets/forecast/roi-analysis/<int:grant_id>', methods=['GET'])
@token_required
def get_roi_analysis(user, grant_id):
    """Get ROI analysis and predictions"""
    try:
        roi_analysis = AssetForecastingService._analyze_roi_predictions(grant_id)
        return jsonify(roi_analysis), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to analyze ROI predictions'}), 500

@forecasting_bp.route('/assets/forecast/seasonal-trends/<int:grant_id>', methods=['GET'])
@token_required
def get_seasonal_trends(user, grant_id):
    """Get seasonal usage and maintenance trends"""
    try:
        seasonal_trends = AssetForecastingService._analyze_seasonal_trends(grant_id)
        return jsonify(seasonal_trends), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to analyze seasonal trends'}), 500

@forecasting_bp.route('/assets/forecast/optimization-recommendations/<int:grant_id>', methods=['GET'])
@token_required
def get_optimization_recommendations(user, grant_id):
    """Get optimization recommendations based on forecasting"""
    try:
        recommendations = AssetForecastingService._generate_optimization_recommendations(grant_id)
        return jsonify(recommendations), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate optimization recommendations'}), 500

# Asset Forecasting Service (additional forecasting methods)
class AssetForecastingService:
    """Service for advanced asset forecasting and predictions"""
    
    @staticmethod
    def _predict_asset_lifecycle(asset) -> Dict:
        """Predict remaining lifecycle for an asset"""
        from datetime import datetime, timedelta
        
        # Calculate age-based predictions
        today = datetime.utcnow().date()
        
        lifecycle_prediction = {
            'asset_id': asset.id,
            'asset_name': asset.name,
            'current_age_days': 0,
            'predicted_end_of_life': None,
            'remaining_useful_life': 0,
            'replacement_probability': 0,
            'maintenance_needs': [],
            'depreciation_schedule': []
        }
        
        if asset.acquisition_date:
            age_days = (today - asset.acquisition_date).days
            lifecycle_prediction['current_age_days'] = age_days
            
            # Predict end of life based on asset category
            category_lifespans = {
                'Vehicle': 3650,  # 10 years
                'IT Equipment': 1825,  # 5 years
                'Lab Equipment': 2555,  # 7 years
                'Office Equipment': 3650,  # 10 years
                'Equipment': 2555  # 7 years default
            }
            
            expected_lifespan = category_lifespans.get(asset.category, 2555)
            remaining_life = max(0, expected_lifespan - age_days)
            
            lifecycle_prediction['predicted_end_of_life'] = (asset.acquisition_date + timedelta(days=expected_lifespan)).isoformat()
            lifecycle_prediction['remaining_useful_life'] = remaining_life
            lifecycle_prediction['replacement_probability'] = min(1.0, age_days / expected_lifespan)
            
            # Maintenance needs prediction
            if remaining_life < 365:  # Less than 1 year remaining
                lifecycle_prediction['maintenance_needs'].append('Comprehensive inspection recommended')
            if remaining_life < 730:  # Less than 2 years remaining
                lifecycle_prediction['maintenance_needs'].append('Plan for replacement budget')
            
            # Depreciation schedule
            if asset.purchase_cost:
                annual_depreciation = asset.purchase_cost / expected_lifespan * 365
                current_depreciated_value = max(0, asset.purchase_cost - (annual_depreciation * age_days))
                
                lifecycle_prediction['depreciation_schedule'] = {
                    'original_cost': asset.purchase_cost,
                    'annual_depreciation': annual_depreciation,
                    'current_depreciated_value': current_depreciated_value,
                    'depreciation_rate': (asset.purchase_cost - current_depreciated_value) / asset.purchase_cost
                }
        
        return lifecycle_prediction
    
    @staticmethod
    def _assess_failure_risk(grant_id: int) -> Dict:
        """Assess failure risk for assets in a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        risk_assessment = {
            'overall_risk_score': 0,
            'high_risk_assets': [],
            'medium_risk_assets': [],
            'low_risk_assets': [],
            'risk_factors': {},
            'mitigation_strategies': []
        }
        
        total_risk_score = 0
        asset_count = len(assets)
        
        for asset in assets:
            asset_risk = AssetForecastingService._calculate_asset_failure_risk(asset)
            
            if asset_risk['risk_score'] >= 70:
                risk_assessment['high_risk_assets'].append(asset_risk)
            elif asset_risk['risk_score'] >= 40:
                risk_assessment['medium_risk_assets'].append(asset_risk)
            else:
                risk_assessment['low_risk_assets'].append(asset_risk)
            
            total_risk_score += asset_risk['risk_score']
        
        if asset_count > 0:
            risk_assessment['overall_risk_score'] = total_risk_score / asset_count
        
        # Risk factors analysis
        risk_assessment['risk_factors'] = AssetForecastingService._analyze_risk_factors(assets)
        
        # Mitigation strategies
        risk_assessment['mitigation_strategies'] = AssetForecastingService._generate_mitigation_strategies(risk_assessment)
        
        return risk_assessment
    
    @staticmethod
    def _calculate_asset_failure_risk(asset) -> Dict:
        """Calculate failure risk for a specific asset"""
        risk_score = 0
        risk_factors = []
        
        # Age factor
        if asset.acquisition_date:
            age_days = (datetime.utcnow().date() - asset.acquisition_date).days
            if age_days > 2555:  # > 7 years
                risk_score += 30
                risk_factors.append('Asset is older than 7 years')
            elif age_days > 1825:  # > 5 years
                risk_score += 20
                risk_factors.append('Asset is older than 5 years')
            elif age_days > 1095:  # > 3 years
                risk_score += 10
                risk_factors.append('Asset is older than 3 years')
        
        # Maintenance factor
        if asset.last_maintenance_date:
            days_since_maintenance = (datetime.utcnow().date() - asset.last_maintenance_date).days
            if days_since_maintenance > 365:
                risk_score += 25
                risk_factors.append('Maintenance is overdue by more than 1 year')
            elif days_since_maintenance > 180:
                risk_score += 15
                risk_factors.append('Maintenance is overdue by more than 6 months')
        else:
            risk_score += 35
            risk_factors.append('No maintenance record found')
        
        # Usage factor
        transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
        if transfer_count > 10:
            risk_score += 15
            risk_factors.append('High usage frequency')
        elif transfer_count == 0 and asset.status == 'ACTIVE':
            risk_score += 10
            risk_factors.append('Asset appears unused')
        
        # Status factor
        if asset.status == 'IN_REPAIR':
            risk_score += 20
            risk_factors.append('Asset currently under repair')
        elif asset.status == 'LOST':
            risk_score += 50
            risk_factors.append('Asset is lost')
        
        # Category-specific risks
        if 'Vehicle' in (asset.category or ''):
            risk_score += 10  # Vehicles have inherent risks
        
        return {
            'asset_id': asset.id,
            'asset_name': asset.name,
            'risk_score': min(100, risk_score),
            'risk_level': 'high' if risk_score >= 70 else 'medium' if risk_score >= 40 else 'low',
            'risk_factors': risk_factors
        }
    
    @staticmethod
    def _analyze_risk_factors(assets) -> Dict:
        """Analyze common risk factors across assets"""
        risk_factors = {
            'aging_assets': 0,
            'poor_maintenance': 0,
            'high_usage': 0,
            'status_issues': 0
        }
        
        for asset in assets:
            if asset.acquisition_date:
                age_days = (datetime.utcnow().date() - asset.acquisition_date).days
                if age_days > 1825:  # > 5 years
                    risk_factors['aging_assets'] += 1
            
            if not asset.last_maintenance_date:
                risk_factors['poor_maintenance'] += 1
            else:
                days_since_maintenance = (datetime.utcnow().date() - asset.last_maintenance_date).days
                if days_since_maintenance > 365:
                    risk_factors['poor_maintenance'] += 1
            
            transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
            if transfer_count > 10:
                risk_factors['high_usage'] += 1
            
            if asset.status in ['IN_REPAIR', 'LOST']:
                risk_factors['status_issues'] += 1
        
        return risk_factors
    
    @staticmethod
    def _generate_mitigation_strategies(risk_assessment: Dict) -> List[str]:
        """Generate mitigation strategies based on risk assessment"""
        strategies = []
        
        if risk_assessment['overall_risk_score'] > 60:
            strategies.append('Implement comprehensive asset risk management program')
        
        if len(risk_assessment['high_risk_assets']) > 0:
            strategies.append('Immediate inspection and maintenance planning for high-risk assets')
        
        risk_factors = risk_assessment['risk_factors']
        if risk_factors.get('aging_assets', 0) > 5:
            strategies.append('Develop asset replacement plan for aging equipment')
        
        if risk_factors.get('poor_maintenance', 0) > 3:
            strategies.append('Implement preventive maintenance schedule')
        
        if risk_factors.get('high_usage', 0) > 2:
            strategies.append('Consider asset redundancy for high-usage equipment')
        
        return strategies
    
    @staticmethod
    def _analyze_roi_predictions(grant_id: int) -> Dict:
        """Analyze ROI predictions for assets"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        roi_analysis = {
            'current_roi': 0,
            'predicted_roi_1yr': 0,
            'predicted_roi_3yr': 0,
            'high_roi_assets': [],
            'low_roi_assets': [],
            'roi_trends': [],
            'recommendations': []
        }
        
        total_investment = sum(a.purchase_cost or 0 for a in assets)
        total_value = 0
        
        for asset in assets:
            # Simplified ROI calculation
            asset_roi = AssetForecastingService._calculate_asset_roi(asset)
            total_value += asset_roi['current_value']
            
            if asset_roi['roi_percentage'] > 0.8:
                roi_analysis['high_roi_assets'].append(asset_roi)
            elif asset_roi['roi_percentage'] < 0.3:
                roi_analysis['low_roi_assets'].append(asset_roi)
        
        if total_investment > 0:
            roi_analysis['current_roi'] = total_value / total_investment
        
        # Predict future ROI (simplified)
        roi_analysis['predicted_roi_1yr'] = roi_analysis['current_roi'] * 0.95  # 5% decline
        roi_analysis['predicted_roi_3yr'] = roi_analysis['current_roi'] * 0.85  # 15% decline
        
        # Recommendations
        if roi_analysis['current_roi'] < 0.5:
            roi_analysis['recommendations'].append('Overall ROI is below 50% - review asset utilization')
        
        if len(roi_analysis['low_roi_assets']) > len(assets) * 0.3:
            roi_analysis['recommendations'].append('Consider disposing of low-ROI assets')
        
        return roi_analysis
    
    @staticmethod
    def _calculate_asset_roi(asset) -> Dict:
        """Calculate ROI for a specific asset"""
        purchase_cost = asset.purchase_cost or 0
        maintenance_cost = 0  # Would calculate from maintenance records
        
        # Current value (simplified)
        current_value = max(0, purchase_cost * 0.7)  # Assume 30% depreciation
        
        roi_percentage = current_value / purchase_cost if purchase_cost > 0 else 0
        
        return {
            'asset_id': asset.id,
            'asset_name': asset.name,
            'purchase_cost': purchase_cost,
            'maintenance_cost': maintenance_cost,
            'current_value': current_value,
            'roi_percentage': roi_percentage
        }
    
    @staticmethod
    def _analyze_seasonal_trends(grant_id: int) -> Dict:
        """Analyze seasonal usage and maintenance trends"""
        # This would analyze historical data for seasonal patterns
        # For now, return placeholder data
        
        seasonal_trends = {
            'maintenance_seasonality': {
                'Q1': 1.2,  # 20% above average
                'Q2': 0.9,  # 10% below average
                'Q3': 1.1,  # 10% above average
                'Q4': 0.8   # 20% below average
            },
            'usage_seasonality': {
                'Q1': 1.0,
                'Q2': 1.1,
                'Q3': 1.2,
                'Q4': 0.9
            },
            'recommendations': [
                'Schedule major maintenance in Q4 when usage is lower',
                'Plan for increased maintenance needs in Q1',
                'Consider asset redistribution based on seasonal patterns'
            ]
        }
        
        return seasonal_trends
    
    @staticmethod
    def _generate_optimization_recommendations(grant_id: int) -> Dict:
        """Generate optimization recommendations based on forecasting"""
        recommendations = {
            'maintenance_optimization': [],
            'utilization_optimization': [],
            'cost_optimization': [],
            'replacement_optimization': []
        }
        
        # Get forecasting data
        maintenance_forecast = AssetAnalyticsService._forecast_maintenance_needs(grant_id)
        replacement_forecast = AssetAnalyticsService._forecast_asset_replacements(grant_id)
        cost_forecast = AssetAnalyticsService._forecast_future_costs(grant_id)
        
        # Maintenance optimization
        if maintenance_forecast['next_quarter']:
            recommendations['maintenance_optimization'].append('Schedule preventive maintenance in Q4 to reduce Q1 workload')
        
        # Utilization optimization
        utilization_analytics = AssetAnalyticsService._get_utilization_analytics(grant_id)
        if len(utilization_analytics['underutilized_assets']) > 0:
            recommendations['utilization_optimization'].append(f'Redeploy {len(utilization_analytics["underutilized_assets"])} underutilized assets')
        
        # Cost optimization
        if cost_forecast['maintenance_costs']['next_year'] > cost_forecast['maintenance_costs']['next_6_months'] * 3:
            recommendations['cost_optimization'].append('Consider asset replacement to reduce long-term maintenance costs')
        
        # Replacement optimization
        if replacement_forecast['next_year']:
            recommendations['replacement_optimization'].append('Plan budget for upcoming asset replacements')
            recommendations['replacement_optimization'].append('Consider phased replacement approach')
        
        return recommendations
