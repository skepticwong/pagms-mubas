from models import db, PriorApprovalRequest, RuleEvaluation, Grant
from services.rule_service import RuleService
from services.workflow_service import WorkflowService
from datetime import datetime

class PriorApprovalService:
    def __init__(self, rule_service=RuleService(), workflow_service=WorkflowService()):
        self.rule_service = rule_service
        self.workflow_service = workflow_service

    def create_request(self, grant_id, requester_id, request_type, category, amount, justification):
        """
        Creates a new prior approval request and evaluates it against the rules.
        """
        # 1. Evaluate Compliance
        context = {
            'amount': amount,
            'category': category.lower(),
            'request_type': request_type,
            'is_pre_approval': True
        }
        
        evaluation = self.rule_service.evaluate_action('EXPENSE_PRE_APPROVAL', context, grant_id)
        
        # 2. Create the Request Record
        request = PriorApprovalRequest(
            grant_id=grant_id,
            requester_id=requester_id,
            request_type=request_type,
            category=category,
            amount=amount,
            justification=justification,
            status='pending'
        )
        
        db.session.add(request)
        db.session.flush() # Get ID
        
        # 3. Handle Outcomes
        if evaluation['outcome'] == 'BLOCK':
            request.status = 'rejected'
            request.rsu_comments = "Request blocked by funder policy."
            db.session.commit()
            return request, evaluation

        if evaluation['outcome'] in ['PASS', 'WARN']:
            # Auto-approve minor items
            request.status = 'approved'
            request.resolved_at = datetime.utcnow()
            db.session.commit()
            return request, evaluation

        # 4. PRIOR_APPROVAL required -> Start Workflow
        steps_config = [
            {'role': 'FINANCE', 'order': 1},
            {'role': 'RSU', 'order': 2}
        ]
        workflow = self.workflow_service.init_workflow('PRIOR_APPROVAL', request.id, steps_config, grant_id=grant_id)
        request.workflow_id = workflow.id
        
        db.session.commit()
        return request, evaluation

    def get_requests_for_grant(self, grant_id):
        return PriorApprovalRequest.query.filter_by(grant_id=grant_id).all()

    def sync_with_workflow(self, request_id, status):
        """Called by Approval Routes when workflow completes/rejects."""
        request = PriorApprovalRequest.query.get(request_id)
        if not request: return
        
        if status == 'completed':
            request.status = 'approved'
            request.resolved_at = datetime.utcnow()
        elif status == 'rejected':
            request.status = 'rejected'
            request.resolved_at = datetime.utcnow()
            
        db.session.commit()
