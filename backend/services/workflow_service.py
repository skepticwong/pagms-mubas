from typing import List, Optional, Dict
from models import db, ApprovalWorkflow, ApprovalStep, ApprovalLog
from repositories.workflow_repository import WorkflowRepository
from datetime import datetime

class WorkflowService:
    """Orchestrates multi-stage serial and parallel approval flows."""

    def __init__(self, workflow_repo: WorkflowRepository = WorkflowRepository):
        self.workflow_repo = workflow_repo

    def init_workflow(self, item_type: str, item_id: int, steps_config: List[Dict], grant_id: int = None) -> ApprovalWorkflow:
        """
        Initializes a new workflow with a set of ordered steps.
        steps_config: List of {'role': 'FINANCE', 'order': 1, 'is_parallel': False}
        """
        workflow = ApprovalWorkflow(
            grant_id=grant_id,
            item_type=item_type,
            item_id=item_id,
            status='in_progress',
            current_step_order=1
        )
        self.workflow_repo.create_workflow(workflow)

        for s in steps_config:
            step = ApprovalStep(
                workflow_id=workflow.id,
                role_required=s['role'],
                order=s['order'],
                is_parallel=s.get('is_parallel', False),
                status='active' if s['order'] == 1 else 'pending'
            )
            self.workflow_repo.save_step(step)

        return workflow

    def process_action(self, workflow_id: int, user_id: int, role: str, action: str, comment: str = None):
        """
        Processes an approval/rejection action for the current active step(s).
        action: 'APPROVE', 'REJECT'
        """
        workflow = self.workflow_repo.find_by_id(workflow_id)
        if not workflow or workflow.status != 'in_progress':
            raise ValueError("Workflow not found or already closed.")

        # Find active steps for this user's role at the current order
        steps = self.workflow_repo.list_steps(workflow_id)
        active_steps = [s for s in steps if s.status == 'active' and s.order == workflow.current_step_order]
        
        target_step = next((s for s in active_steps if s.role_required == role), None)
        if not target_step:
            raise ValueError(f"No active step found for role {role} at current stage.")

        # Log the action
        self.workflow_repo.create_log(ApprovalLog(
            workflow_id=workflow_id,
            user_id=user_id,
            action=action,
            comment=comment
        ))

        if action == 'REJECT':
            target_step.status = 'rejected'
            target_step.resolved_by_id = user_id
            target_step.resolved_at = datetime.utcnow()
            workflow.status = 'rejected'
            self.workflow_repo.save_step(target_step)
            self.workflow_repo.save_workflow(workflow)
            return workflow

        if action == 'APPROVE':
            target_step.status = 'approved'
            target_step.resolved_by_id = user_id
            target_step.resolved_at = datetime.utcnow()
            self.workflow_repo.save_step(target_step)

            # Check if all steps at this order are complete (handles parallel)
            all_at_order = [s for s in steps if s.order == workflow.current_step_order]
            if all(s.status == 'approved' for s in all_at_order):
                # Advance to next order
                next_order = workflow.current_step_order + 1
                next_steps = [s for s in steps if s.order == next_order]
                
                if not next_steps:
                    # No more steps, workflow completed
                    workflow.status = 'completed'
                    workflow.current_step_order = next_order
                else:
                    workflow.current_step_order = next_order
                    # Activate next steps
                    for ns in next_steps:
                        ns.status = 'active'
                        self.workflow_repo.save_step(ns)
                
                self.workflow_repo.save_workflow(workflow)

        return workflow

    def get_workflow_status(self, workflow_id: int) -> dict:
        workflow = self.workflow_repo.find_by_id(workflow_id)
        if not workflow: return None
        steps = self.workflow_repo.list_steps(workflow_id)
        return {
            'workflow': {
                'id': workflow.id,
                'status': workflow.status,
                'current_step': workflow.current_step_order
            },
            'steps': [{
                'id': s.id,
                'role': s.role_required,
                'status': s.status,
                'resolved_by': s.resolved_by_id,
                'order': s.order
            } for s in steps]
        }
