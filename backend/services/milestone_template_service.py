# services/milestone_template_service.py
"""
Service for managing Milestone Templates - Phase 1: Compliance Core
Handles template creation, application, and standard configurations
"""

import json
from models import db, MilestoneTemplate, MilestoneKPI
from datetime import datetime

class MilestoneTemplateService:
    """Service for managing milestone templates"""
    
    @staticmethod
    def get_all_templates():
        """Get all available milestone templates"""
        return MilestoneTemplate.query.all()
    
    @staticmethod
    def get_template_by_id(template_id):
        """Get specific template with its configuration"""
        return MilestoneTemplate.query.get(template_id)
    
    @staticmethod
    def create_template(name, config_json, created_by_user_id):
        """Create a new milestone template"""
        template = MilestoneTemplate(
            name=name,
            config_json=config_json,
            created_by_user_id=created_by_user_id
        )
        
        db.session.add(template)
        db.session.commit()
        return template
    
    @staticmethod
    def apply_template_to_milestone(milestone_id, template_id, target_adjustments=None):
        """Apply template to milestone - create KPIs and suggest assets"""
        # Create KPIs from template
        kpis = MilestoneKPIService.create_kpis_from_template(
            milestone_id, template_id, target_adjustments
        )
        
        # Get suggested assets from template
        template = MilestoneTemplate.query.get(template_id)
        suggested_assets = template.config_json.get('assets', [])
        
        return {
            'kpis_created': len(kpis),
            'suggested_assets': suggested_assets,
            'template_name': template.name,
            'template_config': template.config_json
        }
    
    @staticmethod
    def update_template(template_id, data):
        """Update existing template"""
        template = MilestoneTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Update allowed fields
        if 'name' in data:
            template.name = data['name']
        if 'config_json' in data:
            template.config_json = data['config_json']
        
        db.session.commit()
        return template
    
    @staticmethod
    def delete_template(template_id):
        """Delete template"""
        template = MilestoneTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Check if template is being used by any milestones
        from models import MilestoneKPI
        active_kpis = MilestoneKPI.query.filter_by(
            milestone_id=template_id
        ).count()
        
        if active_kpis > 0:
            raise ValueError(f"Cannot delete template - used by {active_kpis} active milestones")
        
        db.session.delete(template)
        db.session.commit()
        return True
    
    @staticmethod
    def get_template_summary():
        """Get summary of all templates with usage statistics"""
        templates = MilestoneTemplate.query.all()
        
        summary = []
        for template in templates:
            # Count how many milestones use this template
            from models import MilestoneKPI
            usage_count = db.session.query(MilestoneKPI.milestone_id).filter(
                MilestoneKPI.milestone_id.in_(
                    db.session.query(MilestoneKPI.milestone_id).filter(
                        MilestoneKPI.name.in_([k['name'] for k in template.config_json.get('kpis', [])])
                    ).distinct().all()
                )
            ).distinct().count()
            
            summary.append({
                'id': template.id,
                'name': template.name,
                'asset_count': len(template.config_json.get('assets', [])),
                'kpi_count': len(template.config_json.get('kpis', [])),
                'usage_count': usage_count,
                'created_at': template.created_at.isoformat() if template.created_at else None
            })
        
        return summary
    
    @staticmethod
    def validate_template_config(config_json):
        """Validate template configuration structure"""
        required_keys = ['assets', 'kpis']
        
        for key in required_keys:
            if key not in config_json:
                return False, f"Missing required key: {key}"
        
        # Validate assets
        assets = config_json.get('assets', [])
        if not isinstance(assets, list):
            return False, "Assets must be a list"
        
        # Validate KPIs
        kpis = config_json.get('kpis', [])
        if not isinstance(kpis, list):
            return False, "KPIs must be a list"
        
        for kpi in kpis:
            required_kpi_keys = ['name', 'target', 'unit']
            for key in required_kpi_keys:
                if key not in kpi:
                    return False, f"KPI missing required key: {key}"
            
            # Validate target is numeric
            if not isinstance(kpi['target'], (int, float)):
                return False, f"KPI target must be numeric: {kpi['name']}"
        
        return True, "Template configuration is valid"
