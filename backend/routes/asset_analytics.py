"""
Asset Analytics Routes - Advanced analytics and reporting endpoints
"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_analytics_service import AssetAnalyticsService
from services.asset_maintenance_service import AssetMaintenanceService
from services.asset_alert_service import AssetAlertService
from services.asset_disposition_service import AssetDispositionService

analytics_bp = Blueprint('asset_analytics', __name__)

@analytics_bp.route('/assets/analytics/comprehensive/<int:grant_id>', methods=['GET'])
@token_required
def get_comprehensive_analytics(user, grant_id):
    """Get comprehensive analytics for a grant"""
    try:
        analytics = AssetAnalyticsService.get_comprehensive_analytics(grant_id)
        return jsonify(analytics), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch comprehensive analytics'}), 500

@analytics_bp.route('/assets/analytics/overview/<int:grant_id>', methods=['GET'])
@token_required
def get_overview_analytics(user, grant_id):
    """Get overview metrics for assets"""
    try:
        overview = AssetAnalyticsService._get_overview_metrics(grant_id)
        return jsonify(overview), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch overview analytics'}), 500

@analytics_bp.route('/assets/analytics/financial/<int:grant_id>', methods=['GET'])
@token_required
def get_financial_analytics(user, grant_id):
    """Get financial analytics for assets"""
    try:
        financial = AssetAnalyticsService._get_financial_analytics(grant_id)
        return jsonify(financial), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch financial analytics'}), 500

@analytics_bp.route('/assets/analytics/utilization/<int:grant_id>', methods=['GET'])
@token_required
def get_utilization_analytics(user, grant_id):
    """Get utilization analytics for assets"""
    try:
        utilization = AssetAnalyticsService._get_utilization_analytics(grant_id)
        return jsonify(utilization), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch utilization analytics'}), 500

@analytics_bp.route('/assets/analytics/maintenance/<int:grant_id>', methods=['GET'])
@token_required
def get_maintenance_analytics(user, grant_id):
    """Get maintenance analytics for assets"""
    try:
        maintenance = AssetAnalyticsService._get_maintenance_analytics(grant_id)
        return jsonify(maintenance), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch maintenance analytics'}), 500

@analytics_bp.route('/assets/analytics/compliance/<int:grant_id>', methods=['GET'])
@token_required
def get_compliance_analytics(user, grant_id):
    """Get compliance analytics for assets"""
    try:
        compliance = AssetAnalyticsService._get_compliance_analytics(grant_id)
        return jsonify(compliance), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch compliance analytics'}), 500

@analytics_bp.route('/assets/analytics/performance/<int:grant_id>', methods=['GET'])
@token_required
def get_performance_analytics(user, grant_id):
    """Get performance analytics for assets"""
    try:
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        return jsonify(performance), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch performance analytics'}), 500

@analytics_bp.route('/assets/analytics/forecasting/<int:grant_id>', methods=['GET'])
@token_required
def get_forecasting_analytics(user, grant_id):
    """Get forecasting analytics for assets"""
    try:
        forecasting = AssetAnalyticsService._get_forecasting_analytics(grant_id)
        return jsonify(forecasting), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch forecasting analytics'}), 500

# Asset performance scoring
@analytics_bp.route('/assets/<int:asset_id>/performance-score', methods=['GET'])
@token_required
def get_asset_performance_score(user, asset_id):
    """Get performance score for a specific asset"""
    try:
        from models import Asset
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        score = AssetAnalyticsService._calculate_asset_performance_score(asset)
        return jsonify({'performance_score': score}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to calculate performance score'}), 500

# Maintenance trends
@analytics_bp.route('/assets/analytics/maintenance-trends/<int:grant_id>', methods=['GET'])
@token_required
def get_maintenance_trends(user, grant_id):
    """Get maintenance cost trends over time"""
    try:
        trends = AssetAnalyticsService._get_maintenance_cost_trends(grant_id)
        return jsonify(trends), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch maintenance trends'}), 500

# Maintenance by category
@analytics_bp.route('/assets/analytics/maintenance-by-category/<int:grant_id>', methods=['GET'])
@token_required
def get_maintenance_by_category(user, grant_id):
    """Get maintenance performance by asset category"""
    try:
        category_performance = AssetAnalyticsService._get_maintenance_by_category(grant_id)
        return jsonify(category_performance), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch maintenance by category'}), 500

# Predictive maintenance
@analytics_bp.route('/assets/analytics/predictive-maintenance/<int:grant_id>', methods=['GET'])
@token_required
def get_predictive_maintenance(user, grant_id):
    """Get predictive maintenance recommendations"""
    try:
        predictions = AssetAnalyticsService._get_predictive_maintenance(grant_id)
        return jsonify(predictions), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch predictive maintenance'}), 500

# Maintenance efficiency
@analytics_bp.route('/assets/analytics/maintenance-efficiency/<int:grant_id>', methods=['GET'])
@token_required
def get_maintenance_efficiency(user, grant_id):
    """Calculate maintenance efficiency metrics"""
    try:
        efficiency = AssetAnalyticsService._calculate_maintenance_efficiency(grant_id)
        return jsonify(efficiency), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to calculate maintenance efficiency'}), 500

# Forecasting endpoints
@analytics_bp.route('/assets/analytics/forecast-maintenance/<int:grant_id>', methods=['GET'])
@token_required
def forecast_maintenance_needs(user, grant_id):
    """Forecast future maintenance needs"""
    try:
        forecast = AssetAnalyticsService._forecast_maintenance_needs(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast maintenance needs'}), 500

@analytics_bp.route('/assets/analytics/forecast-costs/<int:grant_id>', methods=['GET'])
@token_required
def forecast_future_costs(user, grant_id):
    """Forecast future asset-related costs"""
    try:
        forecast = AssetAnalyticsService._forecast_future_costs(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast future costs'}), 500

@analytics_bp.route('/assets/analytics/forecast-replacements/<int:grant_id>', methods=['GET'])
@token_required
def forecast_asset_replacements(user, grant_id):
    """Forecast asset replacement needs"""
    try:
        forecast = AssetAnalyticsService._forecast_asset_replacements(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast asset replacements'}), 500

@analytics_bp.route('/assets/analytics/forecast-budget/<int:grant_id>', methods=['GET'])
@token_required
def forecast_budget_needs(user, grant_id):
    """Forecast future budget needs for assets"""
    try:
        forecast = AssetAnalyticsService._forecast_budget_needs(grant_id)
        return jsonify(forecast), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to forecast budget needs'}), 500

# Summary dashboard data
@analytics_bp.route('/assets/analytics/dashboard/<int:grant_id>', methods=['GET'])
@token_required
def get_dashboard_data(user, grant_id):
    """Get consolidated dashboard data for assets"""
    try:
        dashboard = {
            'overview': AssetAnalyticsService._get_overview_metrics(grant_id),
            'alerts': AssetAlertService.get_alert_summary(grant_id),
            'maintenance': AssetMaintenanceService.get_maintenance_statistics(grant_id),
            'disposition': AssetDispositionService.get_disposition_summary(grant_id),
            'compliance': AssetAnalyticsService._get_compliance_analytics(grant_id)
        }
        
        return jsonify(dashboard), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

# Comparative analytics
@analytics_bp.route('/assets/analytics/comparison', methods=['POST'])
@token_required
def compare_grants(user):
    """Compare asset analytics across multiple grants"""
    data = request.get_json()
    
    try:
        grant_ids = data.get('grant_ids', [])
        comparison = {}
        
        for grant_id in grant_ids:
            comparison[str(grant_id)] = AssetAnalyticsService._get_overview_metrics(grant_id)
        
        return jsonify({'comparison': comparison}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to compare grants'}), 500

# Asset ranking
@analytics_bp.route('/assets/analytics/ranking/<int:grant_id>', methods=['GET'])
@token_required
def get_asset_ranking(user, grant_id):
    """Get asset ranking by performance score"""
    try:
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        ranking = []
        for asset_id, score in performance['asset_performance_scores'].items():
            from models import Asset
            asset = Asset.query.get(asset_id)
            if asset:
                ranking.append({
                    'id': asset.id,
                    'name': asset.name,
                    'category': asset.category,
                    'performance_score': score,
                    'status': asset.status
                })
        
        # Sort by performance score
        ranking.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return jsonify({'ranking': ranking}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate asset ranking'}), 500
