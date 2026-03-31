"""
Asset Performance Routes - Performance metrics and KPIs endpoints
"""

from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from services.asset_analytics_service import AssetAnalyticsService
from models import Asset, Grant
from typing import Dict, List

performance_bp = Blueprint('asset_performance', __name__)

@performance_bp.route('/assets/performance/<int:grant_id>', methods=['GET'])
@token_required
def get_performance_analytics(user, grant_id):
    """Get comprehensive performance analytics"""
    try:
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        return jsonify(performance), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch performance analytics'}), 500

@performance_bp.route('/assets/<int:asset_id>/performance-score', methods=['GET'])
@token_required
def get_asset_performance_score(user, asset_id):
    """Get performance score for a specific asset"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        score = AssetAnalyticsService._calculate_asset_performance_score(asset)
        
        # Get additional performance details
        performance_details = AssetPerformanceService._get_asset_performance_details(asset)
        
        return jsonify({
            'performance_score': score,
            'details': performance_details
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to calculate performance score'}), 500

@performance_bp.route('/assets/performance/ranking/<int:grant_id>', methods=['GET'])
@token_required
def get_asset_ranking(user, grant_id):
    """Get asset ranking by performance score"""
    try:
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        ranking = []
        for asset_id, score in performance['asset_performance_scores'].items():
            asset = Asset.query.get(asset_id)
            if asset:
                ranking.append({
                    'id': asset.id,
                    'name': asset.name,
                    'category': asset.category,
                    'status': asset.status,
                    'performance_score': score,
                    'performance_grade': AssetPerformanceService._get_performance_grade(score)
                })
        
        # Sort by performance score
        ranking.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return jsonify({'ranking': ranking}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate asset ranking'}), 500

@performance_bp.route('/assets/performance/categories/<int:grant_id>', methods=['GET'])
@token_required
def get_category_performance(user, grant_id):
    """Get performance metrics by asset category"""
    try:
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        category_performance = []
        for category, avg_score in performance['category_performance'].items():
            category_performance.append({
                'category': category,
                'average_score': avg_score,
                'grade': AssetPerformanceService._get_performance_grade(avg_score),
                'asset_count': len([a for a in Asset.query.filter_by(grant_id=grant_id).all() if a.category == category])
            })
        
        # Sort by average score
        category_performance.sort(key=lambda x: x['average_score'], reverse=True)
        
        return jsonify({'category_performance': category_performance}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch category performance'}), 500

@performance_bp.route('/assets/performance/source-types/<int:grant_id>', methods=['GET'])
@token_required
def get_source_type_performance(user, grant_id):
    """Get performance metrics by source type"""
    try:
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        source_performance = []
        for source_type, avg_score in performance['source_type_performance'].items():
            source_performance.append({
                'source_type': source_type,
                'average_score': avg_score,
                'grade': AssetPerformanceService._get_performance_grade(avg_score),
                'asset_count': len([a for a in Asset.query.filter_by(grant_id=grant_id).all() if a.source_type == source_type])
            })
        
        # Sort by average score
        source_performance.sort(key=lambda x: x['average_score'], reverse=True)
        
        return jsonify({'source_performance': source_performance}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch source type performance'}), 500

@performance_bp.route('/assets/performance/trends/<int:grant_id>', methods=['GET'])
@token_required
def get_performance_trends(user, grant_id):
    """Get performance trends over time"""
    try:
        trends = AssetPerformanceService._calculate_performance_trends(grant_id)
        return jsonify(trends), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch performance trends'}), 500

@performance_bp.route('/assets/performance/kpi/<int:grant_id>', methods=['GET'])
@token_required
def get_performance_kpis(user, grant_id):
    """Get key performance indicators"""
    try:
        kpis = AssetPerformanceService._calculate_kpis(grant_id)
        return jsonify(kpis), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch KPIs'}), 500

@performance_bp.route('/assets/performance/benchmark/<int:grant_id>', methods=['GET'])
@token_required
def get_performance_benchmark(user, grant_id):
    """Get performance benchmarking against similar grants"""
    try:
        benchmark = AssetPerformanceService._calculate_performance_benchmark(grant_id)
        return jsonify(benchmark), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch performance benchmark'}), 500

@performance_bp.route('/assets/performance/improvement-recommendations/<int:grant_id>', methods=['GET'])
@token_required
def get_improvement_recommendations(user, grant_id):
    """Get performance improvement recommendations"""
    try:
        recommendations = AssetPerformanceService._generate_improvement_recommendations(grant_id)
        return jsonify(recommendations), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate recommendations'}), 500

@performance_bp.route('/assets/performance/dashboard/<int:grant_id>', methods=['GET'])
@token_required
def get_performance_dashboard(user, grant_id):
    """Get performance dashboard data"""
    try:
        dashboard = {
            'overview': AssetPerformanceService._get_performance_overview(grant_id),
            'top_performers': AssetPerformanceService._get_top_performers(grant_id),
            'underperformers': AssetPerformanceService._get_underperformers(grant_id),
            'performance_trends': AssetPerformanceService._calculate_performance_trends(grant_id),
            'kpis': AssetPerformanceService._calculate_kpis(grant_id)
        }
        
        return jsonify(dashboard), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch performance dashboard'}), 500

# Asset Performance Service (additional performance methods)
class AssetPerformanceService:
    """Service for advanced asset performance metrics"""
    
    @staticmethod
    def _get_asset_performance_details(asset) -> Dict:
        """Get detailed performance metrics for an asset"""
        details = {
            'basic_metrics': {
                'age_days': 0,
                'maintenance_count': 0,
                'transfer_count': 0,
                'utilization_score': 0
            },
            'performance_factors': {
                'age_factor': 0,
                'maintenance_factor': 0,
                'utilization_factor': 0,
                'compliance_factor': 0,
                'value_factor': 0
            },
            'recommendations': []
        }
        
        # Calculate basic metrics
        from datetime import datetime
        if asset.acquisition_date:
            details['basic_metrics']['age_days'] = (datetime.utcnow().date() - asset.acquisition_date).days
        
        from models import AssetMaintenance, AssetTransfer
        details['basic_metrics']['maintenance_count'] = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
        details['basic_metrics']['transfer_count'] = AssetTransfer.query.filter_by(asset_id=asset.id).count()
        details['basic_metrics']['utilization_score'] = AssetPerformanceService._calculate_utilization_score(asset)
        
        # Calculate performance factors
        details['performance_factors'] = AssetPerformanceService._calculate_performance_factors(asset)
        
        # Generate recommendations
        details['recommendations'] = AssetPerformanceService._generate_asset_recommendations(asset, details)
        
        return details
    
    @staticmethod
    def _calculate_performance_factors(asset) -> Dict:
        """Calculate individual performance factors"""
        factors = {
            'age_factor': 0,
            'maintenance_factor': 0,
            'utilization_factor': 0,
            'compliance_factor': 0,
            'value_factor': 0
        }
        
        from datetime import datetime
        
        # Age factor (newer is better)
        if asset.acquisition_date:
            age_days = (datetime.utcnow().date() - asset.acquisition_date).days
            if age_days < 365:
                factors['age_factor'] = 25
            elif age_days < 1095:
                factors['age_factor'] = 15
            elif age_days < 1825:
                factors['age_factor'] = 5
            elif age_days > 1825:
                factors['age_factor'] = -10
        
        # Maintenance factor
        from models import AssetMaintenance
        maintenance_count = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
        if maintenance_count > 0:
            last_maintenance = AssetMaintenance.query.filter_by(asset_id=asset.id).order_by(AssetMaintenance.performed_date.desc()).first()
            if last_maintenance and last_maintenance.performed_date:
                days_since_maintenance = (datetime.utcnow().date() - last_maintenance.performed_date).days
                if days_since_maintenance < 90:
                    factors['maintenance_factor'] = 20
                elif days_since_maintenance < 365:
                    factors['maintenance_factor'] = 10
                elif days_since_maintenance > 365:
                    factors['maintenance_factor'] = -15
        else:
            factors['maintenance_factor'] = -20
        
        # Utilization factor
        transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
        if transfer_count > 5:
            factors['utilization_factor'] = 15
        elif transfer_count > 2:
            factors['utilization_factor'] = 10
        elif transfer_count == 0 and asset.status == 'ACTIVE':
            factors['utilization_factor'] = -10
        
        # Compliance factor
        from services.asset_alert_service import AssetAlertService
        alerts = AssetAlertService.generate_all_alerts(asset.grant_id)
        asset_alerts = [a for a in alerts if a['asset_id'] == asset.id]
        if len(asset_alerts) == 0:
            factors['compliance_factor'] = 15
        elif len(asset_alerts) > 2:
            factors['compliance_factor'] = -15
        
        # Value factor
        if asset.purchase_cost and asset.purchase_cost > 10000:
            factors['value_factor'] = 5
        
        return factors
    
    @staticmethod
    def _calculate_utilization_score(asset) -> float:
        """Calculate utilization score for an asset"""
        score = 0
        
        # Transfer frequency
        from models import AssetTransfer
        transfer_count = AssetTransfer.query.filter_by(asset_id=asset.id).count()
        if transfer_count > 5:
            score += 30
        elif transfer_count > 2:
            score += 20
        elif transfer_count > 0:
            score += 10
        
        # Custody duration
        custody_days = AssetPerformanceService._calculate_custody_duration(asset.id)
        if custody_days > 365:
            score += 25
        elif custody_days > 180:
            score += 15
        elif custody_days > 30:
            score += 10
        
        # Maintenance activity
        from models import AssetMaintenance
        maintenance_count = AssetMaintenance.query.filter_by(asset_id=asset.id).count()
        if maintenance_count > 3:
            score += 25
        elif maintenance_count > 1:
            score += 15
        elif maintenance_count > 0:
            score += 10
        
        # Current status
        if asset.status == 'ACTIVE':
            score += 20
        elif asset.status in ['IN_REPAIR', 'LENDED']:
            score += 10
        
        return min(100, score)
    
    @staticmethod
    def _calculate_custody_duration(asset_id: int) -> int:
        """Calculate total days asset has been in custody"""
        from models import AssetTransfer
        transfers = AssetTransfer.query.filter_by(asset_id=asset_id).order_by(AssetTransfer.created_at).all()
        
        if not transfers:
            return 0
        
        total_days = 0
        from datetime import datetime
        for i, transfer in enumerate(transfers):
            start_date = transfer.created_at.date()
            if i < len(transfers) - 1:
                end_date = transfers[i + 1].created_at.date()
            else:
                end_date = datetime.utcnow().date()
            
            total_days += (end_date - start_date).days
        
        return total_days
    
    @staticmethod
    def _generate_asset_recommendations(asset, details: Dict) -> List[str]:
        """Generate recommendations for improving asset performance"""
        recommendations = []
        
        # Age-based recommendations
        if details['basic_metrics']['age_days'] > 1825:
            recommendations.append('Consider asset replacement - asset is over 5 years old')
        elif details['basic_metrics']['age_days'] > 1095:
            recommendations.append('Plan for asset replacement in next 2 years')
        
        # Maintenance-based recommendations
        if details['basic_metrics']['maintenance_count'] == 0:
            recommendations.append('Establish regular maintenance schedule')
        elif details['performance_factors']['maintenance_factor'] < 0:
            recommendations.append('Schedule maintenance - overdue or infrequent service')
        
        # Utilization-based recommendations
        if details['basic_metrics']['transfer_count'] == 0 and asset.status == 'ACTIVE':
            recommendations.append('Review asset utilization - appears unused')
        elif details['performance_factors']['utilization_factor'] < 0:
            recommendations.append('Consider asset redistribution to improve utilization')
        
        # Compliance-based recommendations
        if details['performance_factors']['compliance_factor'] < 0:
            recommendations.append('Address compliance issues to improve performance')
        
        return recommendations
    
    @staticmethod
    def _get_performance_grade(score: float) -> str:
        """Get performance grade based on score"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 45:
            return 'D+'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    @staticmethod
    def _calculate_performance_trends(grant_id: int) -> Dict:
        """Calculate performance trends over time"""
        # This would analyze historical performance data
        # For now, return placeholder data
        trends = {
            'period': '6 months',
            'trend_direction': 'stable',
            'average_score_change': 2.5,
            'performance_momentum': 0.1,
            'monthly_scores': {
                '2024-10': 75.2,
                '2024-11': 76.8,
                '2024-12': 77.1,
                '2025-01': 77.9,
                '2025-02': 78.3,
                '2025-03': 78.7
            }
        }
        
        return trends
    
    @staticmethod
    def _calculate_kpis(grant_id: int) -> Dict:
        """Calculate key performance indicators"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        kpis = {
            'total_assets': len(assets),
            'average_performance_score': 0,
            'high_performers_percentage': 0,
            'low_performers_percentage': 0,
            'compliance_rate': 0,
            'utilization_rate': 0,
            'maintenance_effectiveness': 0
        }
        
        if not assets:
            return kpis
        
        # Calculate average performance score
        total_score = 0
        high_performers = 0
        low_performers = 0
        compliant_assets = 0
        utilized_assets = 0
        
        for asset in assets:
            score = AssetAnalyticsService._calculate_asset_performance_score(asset)
            total_score += score
            
            if score >= 80:
                high_performers += 1
            elif score < 60:
                low_performers += 1
            
            # Compliance check
            from services.asset_alert_service import AssetAlertService
            alerts = AssetAlertService.generate_all_alerts(grant_id)
            asset_alerts = [a for a in alerts if a['asset_id'] == asset.id]
            if len(asset_alerts) == 0:
                compliant_assets += 1
            
            # Utilization check
            from models import AssetTransfer
            if AssetTransfer.query.filter_by(asset_id=asset.id).count() > 0:
                utilized_assets += 1
        
        kpis['average_performance_score'] = total_score / len(assets)
        kpis['high_performers_percentage'] = (high_performers / len(assets)) * 100
        kpis['low_performers_percentage'] = (low_performers / len(assets)) * 100
        kpis['compliance_rate'] = (compliant_assets / len(assets)) * 100
        kpis['utilization_rate'] = (utilized_assets / len(assets)) * 100
        
        # Maintenance effectiveness (simplified)
        from models import AssetMaintenance
        total_maintenance = AssetMaintenance.query.join(Asset).filter(Asset.grant_id == grant_id).count()
        total_assets = len(assets)
        kpis['maintenance_effectiveness'] = (total_maintenance / total_assets) if total_assets > 0 else 0
        
        return kpis
    
    @staticmethod
    def _calculate_performance_benchmark(grant_id: int) -> Dict:
        """Calculate performance benchmark against similar grants"""
        # This would compare against similar grants
        # For now, return placeholder data
        benchmark = {
            'grant_performance': 78.5,
            'peer_average': 75.2,
            'peer_percentile': 75,
            'performance_ranking': 'Above Average',
            'benchmark_categories': {
                'overall': {'current': 78.5, 'benchmark': 75.2, 'percentile': 75},
                'maintenance': {'current': 82.1, 'benchmark': 78.5, 'percentile': 80},
                'utilization': {'current': 76.3, 'benchmark': 74.8, 'percentile': 70},
                'compliance': {'current': 85.7, 'benchmark': 82.3, 'percentile': 85}
            }
        }
        
        return benchmark
    
    @staticmethod
    def _generate_improvement_recommendations(grant_id: int) -> Dict:
        """Generate performance improvement recommendations"""
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'estimated_impact': {},
            'implementation_timeline': {}
        }
        
        # High priority recommendations
        if performance['overall_performance_score'] < 70:
            recommendations['high_priority'].append('Implement comprehensive asset performance improvement program')
            recommendations['estimated_impact']['performance_improvement'] = '15-25%'
            recommendations['implementation_timeline']['performance_improvement'] = '3-6 months'
        
        # Medium priority recommendations
        if len(performance['underperformers']) > len(performance['asset_performance_scores']) * 0.2:
            recommendations['medium_priority'].append('Focus on bottom 20% performing assets')
            recommendations['estimated_impact']['underperformer_focus'] = '10-15%'
            recommendations['implementation_timeline']['underperformer_focus'] = '1-3 months'
        
        # Low priority recommendations
        if performance['overall_performance_score'] > 80:
            recommendations['low_priority'].append('Maintain current performance levels with continuous monitoring')
            recommendations['estimated_impact']['maintenance'] = '2-5%'
            recommendations['implementation_timeline']['maintenance'] = 'Ongoing'
        
        return recommendations
    
    @staticmethod
    def _get_performance_overview(grant_id: int) -> Dict:
        """Get performance overview summary"""
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        overview = {
            'overall_score': performance['overall_performance_score'],
            'grade': AssetPerformanceService._get_performance_grade(performance['overall_performance_score']),
            'total_assets': len(performance['asset_performance_scores']),
            'top_performers_count': len(performance['top_performers']),
            'underperformers_count': len(performance['underperformers']),
            'performance_distribution': {
                'excellent': len([s for s in performance['asset_performance_scores'].values() if s >= 90]),
                'good': len([s for s in performance['asset_performance_scores'].values() if 80 <= s < 90]),
                'average': len([s for s in performance['asset_performance_scores'].values() if 70 <= s < 80]),
                'below_average': len([s for s in performance['asset_performance_scores'].values() if s < 70])
            }
        }
        
        return overview
    
    @staticmethod
    def _get_top_performers(grant_id: int, limit: int = 10) -> List[Dict]:
        """Get top performing assets"""
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        top_performers = []
        for asset_id, score in performance['top_performers']:
            asset = Asset.query.get(asset_id)
            if asset:
                top_performers.append({
                    'id': asset.id,
                    'name': asset.name,
                    'category': asset.category,
                    'performance_score': score,
                    'grade': AssetPerformanceService._get_performance_grade(score)
                })
        
        return top_performers[:limit]
    
    @staticmethod
    def _get_underperformers(grant_id: int, limit: int = 10) -> List[Dict]:
        """Get underperforming assets"""
        performance = AssetAnalyticsService._get_performance_analytics(grant_id)
        
        underperformers = []
        for asset_id, score in performance['underperformers']:
            asset = Asset.query.get(asset_id)
            if asset:
                underperformers.append({
                    'id': asset.id,
                    'name': asset.name,
                    'category': asset.category,
                    'performance_score': score,
                    'grade': AssetPerformanceService._get_performance_grade(score)
                })
        
        return underperformers[:limit]
