# services/grant_kpi_service.py
"""Grant KPI Service - Phase 1: Grant-Level KPI Management
Service for managing grant-level Key Performance Indicators"""

from models import db, GrantKPI, MilestoneKPI, Grant, User
from datetime import datetime

class GrantKPIService:
    """Service for grant-level KPI operations"""
    
    @staticmethod
    def create_grant_kpis(grant_id, kpis_data, user_id):
        """Create master KPI list for grant during initialization"""
        try:
            created_kpis = []
            
            for kpi_data in kpis_data:
                grant_kpi = GrantKPI(
                    grant_id=grant_id,
                    name=kpi_data['name'],
                    description=kpi_data.get('description', ''),
                    unit=kpi_data.get('unit', 'count'),
                    category=kpi_data.get('category', 'research'),
                    grant_wide_target=kpi_data['grant_wide_target'],
                    baseline_value=kpi_data.get('baseline_value', 0),
                    created_by_user_id=user_id
                )
                
                db.session.add(grant_kpi)
                created_kpis.append(grant_kpi)
            
            db.session.commit()
            
            return {
                'success': True,
                'kpis': [kpi.to_dict() for kpi in created_kpis],
                'message': f'Created {len(created_kpis)} grant KPIs'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create grant KPIs'
            }
    
    @staticmethod
    def get_grant_kpis(grant_id):
        """Get all master KPIs for a grant"""
        try:
            kpis = GrantKPI.query.filter_by(grant_id=grant_id).all()
            return {
                'success': True,
                'kpis': [kpi.to_dict() for kpi in kpis]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get grant KPIs'
            }
    
    @staticmethod
    def get_grant_progress(grant_id):
        """Calculate overall grant achievement across all KPIs"""
        try:
            kpis = GrantKPI.query.filter_by(grant_id=grant_id).all()
            
            total_achievement = 0
            kpi_count = len(kpis)
            category_breakdown = {}
            
            for kpi in kpis:
                # Category breakdown
                if kpi.category not in category_breakdown:
                    category_breakdown[kpi.category] = {
                        'total_target': 0,
                        'total_actual': 0,
                        'achievement_pct': 0,
                        'kpis': []
                    }
                
                category_breakdown[kpi.category]['total_target'] += kpi.grant_wide_target
                category_breakdown[kpi.category]['total_actual'] += kpi.total_actual
                category_breakdown[kpi.category]['kpis'].append(kpi.to_dict())
                
                total_achievement += kpi.achievement_pct
            
            # Calculate category percentages
            for category, data in category_breakdown.items():
                if data['total_target'] > 0:
                    data['achievement_pct'] = (data['total_actual'] / data['total_target']) * 100
            
            overall_achievement = total_achievement / kpi_count if kpi_count > 0 else 0
            
            return {
                'success': True,
                'overall_achievement_pct': overall_achievement,
                'total_kpis': kpi_count,
                'category_breakdown': category_breakdown,
                'kpis': [kpi.to_dict() for kpi in kpis]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to calculate grant progress'
            }
    
    @staticmethod
    def get_available_grant_kpis(grant_id):
        """Get master KPIs that can be allocated to milestones"""
        try:
            kpis = GrantKPI.query.filter_by(grant_id=grant_id).all()
            return {
                'success': True,
                'available_kpis': [kpi.to_dict() for kpi in kpis]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get available grant KPIs'
            }
    
    @staticmethod
    def allocate_kpi_to_milestone(grant_kpi_id, milestone_id, milestone_target):
        """Allocate portion of grant KPI to milestone"""
        try:
            # Check if allocation already exists
            existing = MilestoneKPI.query.filter_by(
                grant_kpi_id=grant_kpi_id,
                milestone_id=milestone_id
            ).first()
            
            if existing:
                # Update existing allocation
                existing.milestone_target = milestone_target
                db.session.commit()
                return {
                    'success': True,
                    'allocation': existing.to_dict(),
                    'message': 'Updated existing KPI allocation'
                }
            else:
                # Create new allocation
                allocation = MilestoneKPI(
                    grant_kpi_id=grant_kpi_id,
                    milestone_id=milestone_id,
                    milestone_target=milestone_target
                )
                
                db.session.add(allocation)
                db.session.commit()
                
                return {
                    'success': True,
                    'allocation': allocation.to_dict(),
                    'message': 'Created new KPI allocation'
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to allocate KPI to milestone'
            }
    
    @staticmethod
    def remove_kpi_allocation(milestone_kpi_id):
        """Remove KPI allocation from milestone"""
        try:
            allocation = MilestoneKPI.query.get(milestone_kpi_id)
            if not allocation:
                return {
                    'success': False,
                    'message': 'KPI allocation not found'
                }
            
            db.session.delete(allocation)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'KPI allocation removed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to remove KPI allocation'
            }
    
    @staticmethod
    def update_grant_kpi(grant_kpi_id, kpi_data):
        """Update grant KPI (admin only)"""
        try:
            grant_kpi = GrantKPI.query.get(grant_kpi_id)
            if not grant_kpi:
                return {
                    'success': False,
                    'message': 'Grant KPI not found'
                }
            
            # Update allowed fields
            if 'name' in kpi_data:
                grant_kpi.name = kpi_data['name']
            if 'description' in kpi_data:
                grant_kpi.description = kpi_data['description']
            if 'unit' in kpi_data:
                grant_kpi.unit = kpi_data['unit']
            if 'category' in kpi_data:
                grant_kpi.category = kpi_data['category']
            if 'grant_wide_target' in kpi_data:
                grant_kpi.grant_wide_target = kpi_data['grant_wide_target']
            if 'baseline_value' in kpi_data:
                grant_kpi.baseline_value = kpi_data['baseline_value']
            
            db.session.commit()
            
            return {
                'success': True,
                'kpi': grant_kpi.to_dict(),
                'message': 'Grant KPI updated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update grant KPI'
            }
    
    @staticmethod
    def delete_grant_kpi(grant_kpi_id):
        """Delete grant KPI (admin only)"""
        try:
            grant_kpi = GrantKPI.query.get(grant_kpi_id)
            if not grant_kpi:
                return {
                    'success': False,
                    'message': 'Grant KPI not found'
                }
            
            # Check if KPI has allocations
            allocations = MilestoneKPI.query.filter_by(grant_kpi_id=grant_kpi_id).count()
            if allocations > 0:
                return {
                    'success': False,
                    'message': f'Cannot delete KPI with {allocations} milestone allocations'
                }
            
            db.session.delete(grant_kpi)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Grant KPI deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to delete grant KPI'
            }
