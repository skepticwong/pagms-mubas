# services/milestone_kpi_service.py
"""
Service for managing Milestone KPIs - Phase 1: Compliance Core
Handles KPI creation, updates, and validation for milestone completion
"""

import json
from models import db, MilestoneKPI, MilestoneTemplate, Milestone
from datetime import datetime

class MilestoneKPIService:
    """Service for managing milestone KPIs"""
    
    @staticmethod
    def create_kpis_from_template(milestone_id, template_id, target_adjustments=None):
        """Create KPIs for milestone from template"""
        template = MilestoneTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        kpis_created = []
        for kpi_config in template.config_json.get('kpis', []):
            # Apply target adjustments if provided
            target_value = kpi_config['target']
            if target_adjustments and kpi_config['name'] in target_adjustments:
                target_value = target_adjustments[kpi_config['name']]
            
            kpi = MilestoneKPI(
                milestone_id=milestone_id,
                name=kpi_config['name'],
                target_value=target_value,
                unit=kpi_config['unit']
            )
            db.session.add(kpi)
            kpis_created.append(kpi)
        
        db.session.commit()
        return kpis_created
    
    @staticmethod
    def update_kpi_results(milestone_id, kpi_results):
        """Update KPI actual values and calculate achievements"""
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            raise ValueError("Milestone not found")
        
        for result in kpi_results:
            kpi = MilestoneKPI.query.filter_by(
                milestone_id=milestone_id,
                name=result['name']
            ).first()
            
            if kpi:
                kpi.actual_value = result['actual_value']
                kpi.evidence_link = result.get('evidence_link')
                kpi.calculate_achievement()
        
        db.session.commit()
        return milestone.kpis
    
    @staticmethod
    def validate_milestone_kpi_completion(milestone_id):
        """Check if all KPIs have actual values"""
        kpis = MilestoneKPI.query.filter_by(milestone_id=milestone_id).all()
        
        for kpi in kpis:
            if kpi.actual_value is None:
                return False, f"KPI '{kpi.name}' requires actual value"
        
        return True, "All KPIs completed"
    
    @staticmethod
    def get_milestone_kpis(milestone_id):
        """Get all KPIs for a milestone"""
        return MilestoneKPI.query.filter_by(milestone_id=milestone_id).all()
    
    @staticmethod
    def get_kpi_by_id(kpi_id):
        """Get specific KPI by ID"""
        return MilestoneKPI.query.get(kpi_id)
    
    @staticmethod
    def update_kpi(kpi_id, data):
        """Update specific KPI"""
        kpi = MilestoneKPI.query.get(kpi_id)
        if not kpi:
            raise ValueError("KPI not found")
        
        # Update allowed fields
        if 'name' in data:
            kpi.name = data['name']
        if 'target_value' in data:
            kpi.target_value = data['target_value']
        if 'unit' in data:
            kpi.unit = data['unit']
        if 'actual_value' in data:
            kpi.actual_value = data['actual_value']
            kpi.calculate_achievement()
        
        db.session.commit()
        return kpi
    
    @staticmethod
    def delete_kpi(kpi_id):
        """Delete KPI"""
        kpi = MilestoneKPI.query.get(kpi_id)
        if not kpi:
            raise ValueError("KPI not found")
        
        db.session.delete(kpi)
        db.session.commit()
        return True
    
    @staticmethod
    def get_milestone_kpi_summary(milestone_id):
        """Get summary statistics for milestone KPIs"""
        kpis = MilestoneKPI.query.filter_by(milestone_id=milestone_id).all()
        
        if not kpis:
            return {
                'total_kpis': 0,
                'completed_kpis': 0,
                'achieved_kpis': 0,
                'partial_kpis': 0,
                'missed_kpis': 0,
                'overall_achievement': 0
            }
        
        total_kpis = len(kpis)
        completed_kpis = len([k for k in kpis if k.actual_value is not None])
        achieved_kpis = len([k for k in kpis if k.status == 'ACHIEVED'])
        partial_kpis = len([k for k in kpis if k.status == 'PARTIAL'])
        missed_kpis = len([k for k in kpis if k.status == 'MISSED'])
        
        # Calculate overall achievement
        total_achievement = sum([k.achievement_pct or 0 for k in kpis])
        overall_achievement = total_achievement / total_kpis if total_kpis > 0 else 0
        
        return {
            'total_kpis': total_kpis,
            'completed_kpis': completed_kpis,
            'achieved_kpis': achieved_kpis,
            'partial_kpis': partial_kpis,
            'missed_kpis': missed_kpis,
            'overall_achievement': round(overall_achievement, 1)
        }
