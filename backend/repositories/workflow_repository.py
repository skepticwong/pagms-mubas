from typing import Optional, List
from models import db, ApprovalWorkflow, ApprovalStep, ApprovalLog

class WorkflowRepository:
    """CRUD helpers for multi-stage approval workflows."""

    @staticmethod
    def create_workflow(workflow: ApprovalWorkflow) -> ApprovalWorkflow:
        db.session.add(workflow)
        db.session.commit()
        return workflow

    @staticmethod
    def find_by_id(workflow_id: int) -> Optional[ApprovalWorkflow]:
        return ApprovalWorkflow.query.get(workflow_id)

    @staticmethod
    def list_steps(workflow_id: int) -> List[ApprovalStep]:
        return ApprovalStep.query.filter_by(workflow_id=workflow_id).order_by(ApprovalStep.order).all()

    @staticmethod
    def save_step(step: ApprovalStep) -> ApprovalStep:
        db.session.add(step)
        db.session.commit()
        return step

    @staticmethod
    def create_log(log: ApprovalLog) -> ApprovalLog:
        db.session.add(log)
        db.session.commit()
        return log

    @staticmethod
    def save_workflow(workflow: ApprovalWorkflow) -> ApprovalWorkflow:
        db.session.add(workflow)
        db.session.commit()
        return workflow
