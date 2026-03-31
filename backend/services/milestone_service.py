from models import db, Milestone, Task, Deliverable, AuditLog, AuditTrail
from datetime import datetime
from services.rule_service import RuleService
from services.audit_service import AuditService
from services.health_score_service import HealthScoreService

class MilestoneService:
    @staticmethod
    def update_milestone(milestone_id, data, updater_id):
        """Enhanced milestone update with KPI and asset validation"""
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            raise ValueError("Milestone not found")
        
        # Check if milestone is being marked as completed
        if data.get('status') == 'COMPLETED':
            # Gate 1: Asset Validation
            from services.asset_assignment_service import AssetAssignmentService
            asset_validation, asset_message = AssetAssignmentService.validate_milestone_assets(milestone_id)
            if not asset_validation:
                raise ValueError(f"Cannot complete milestone - {asset_message}")
            
            # Gate 3: Compliance Engine 2.0
            milestone_context = {
                'title': milestone.title,
                'status': 'COMPLETED',
                'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
                'action_type': 'MILESTONE_COMPLETION'
            }
            rule_result = RuleService.evaluate_action('MILESTONE', milestone_context, milestone.grant_id)
            if rule_result['outcome'] == 'BLOCK':
                reasons = "; ".join([r['guidance'] for r in rule_result['triggered_rules']])
                raise ValueError(f"Compliance Block: {reasons}")
        
        # Update milestone properties
        for key, value in data.items():
            if hasattr(milestone, key) and key not in ['id', 'created_at']:
                setattr(milestone, key, value)
        
        milestone.updated_at = datetime.utcnow()
        
        # Log Audit
        AuditService.log_action(
            user_id=updater_id,
            action='MILESTONE_UPDATED',
            entity_type='MILESTONE',
            entity_id=milestone.id,
            details={'status': data.get('status')}
        )
        
        # Finalize
        db.session.commit()
        
        # Calculate health score if status changed to completed
        if data.get('status') == 'COMPLETED':
            HealthScoreService.calculate_score(milestone.grant_id)
        
        return milestone
    
    @staticmethod
    def get_milestone_with_kpis(milestone_id):
        """Get milestone with all its KPIs"""
        milestone = Milestone.query.get(milestone_id)
        if milestone:
            milestone_dict = milestone.to_dict()
            from services.milestone_kpi_service import MilestoneKPIService
            kpis = MilestoneKPIService.get_milestone_kpis(milestone_id)
            milestone_dict['kpis'] = [kpi.to_dict() for kpi in kpis]
            return milestone_dict
        return None
    
    @staticmethod
    def update_milestone_status(milestone_id):
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return
        
        # Check Tasks
        total_tasks = len(milestone.tasks)
        completed_tasks = sum(1 for t in milestone.tasks if t.status.lower() == 'completed')
        
        # Check Deliverables
        total_deliverables = len(milestone.deliverables)
        verified_deliverables = sum(1 for d in milestone.deliverables if d.status == 'VERIFIED')
        
        # Logic: Milestone is complete ONLY if all tasks are done AND all deliverables are verified
        if total_tasks > 0 or total_deliverables > 0:
            tasks_done = (completed_tasks == total_tasks) if total_tasks > 0 else True
            deliverables_done = (verified_deliverables == total_deliverables) if total_deliverables > 0 else True
            
            if tasks_done and deliverables_done:
                if milestone.status != 'COMPLETED':
                    milestone.status = 'COMPLETED'
                    milestone.completion_date = datetime.utcnow()
                    db.session.commit() # Commit status change first
                    
                    # Check for Tranche Readiness (Orphan Prevention & Soft Lock)
                    if milestone.triggers_tranche:
                        grant = milestone.grant
                        if grant.can_release_tranche(milestone.triggers_tranche):
                            from services.notification_service import NotificationService
                            NotificationService.notify_role(
                                'Finance', 
                                'TRANCHE_READY', 
                                f"Tranche {milestone.triggers_tranche} for Grant {grant.grant_code} is READY for release.",
                                {'grant_id': grant.id, 'tranche': milestone.triggers_tranche}
                            )
                            NotificationService.notify_role(
                                'RSU', 
                                'TRANCHE_READY', 
                                f"Tranche {milestone.triggers_tranche} for Grant {grant.grant_code} is READY for release.",
                                {'grant_id': grant.id, 'tranche': milestone.triggers_tranche}
                            )
            elif completed_tasks > 0 or verified_deliverables > 0:
                milestone.status = 'IN_PROGRESS'
            else:
                milestone.status = 'NOT_STARTED'
        else:
            # No tasks or deliverables, status depends on other factors or stays NOT_STARTED
            milestone.status = 'NOT_STARTED'
                
        db.session.commit()
        return milestone

    @staticmethod
    def get_milestones_by_grant(grant_id):
        return Milestone.query.filter_by(grant_id=grant_id).all()

    @staticmethod
    def get_milestone_details(milestone_id):
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            return None
        
        data = milestone.to_dict()
        data['tasks'] = [t.to_dict() for t in milestone.tasks]
        data['deliverables'] = [d.to_dict() for d in milestone.deliverables]
        return data

    @staticmethod
    def reopen_milestone(milestone_id, user_id):
        milestone = Milestone.query.get(milestone_id)
        if not milestone:
            raise ValueError(f"Milestone with ID {milestone_id} not found.")
        
        # Authorization: Only PI of the grant can reopen
        if milestone.grant.pi_id != user_id:
            raise ValueError("Only the Principal Investigator can reopen a milestone.")
            
        if milestone.status != 'COMPLETED':
            return milestone # Already open or not started
            
        milestone.status = 'IN_PROGRESS'
        milestone.completion_date = None
        
        # Log the action
        log = AuditLog(
            user_id=user_id,
            action="REOPEN_MILESTONE",
            resource_type="Milestone",
            resource_id=milestone_id,
            details=f"Milestone '{milestone.title}' reopened by PI.",
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        return milestone
