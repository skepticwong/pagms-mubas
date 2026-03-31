from flask import Blueprint, request, jsonify, session
from models import db, ApprovalWorkflow, ApprovalStep, User, BudgetVirement, ExpenseClaim, PriorApprovalRequest, BudgetCategory
from services.workflow_service import WorkflowService
from services.virement_service import VirementService
from services.prior_approval_service import PriorApprovalService

approvals_bp = Blueprint('approvals', __name__)
workflow_service = WorkflowService()
virement_service = VirementService()
prior_approval_service = PriorApprovalService()

@approvals_bp.route('/approvals/pending', methods=['GET'])
def get_pending_approvals():
    """List all steps pending for the current user's role."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    # System roles
    roles = [user.role.upper()]
    
    # Check for grant-level roles (Co-PI with budget authority)
    from models import GrantTeam
    co_pi_grants = GrantTeam.query.filter_by(
        user_id=user.id, 
        role='Co-PI', 
        budget_authority=True, 
        status='active'
    ).all()
    co_pi_grant_ids = [cp.grant_id for cp in co_pi_grants]

    # Find pending steps where role matches system role
    pending_steps = ApprovalStep.query.filter(
        ApprovalStep.status == 'active',
        ApprovalStep.role_required.in_(roles)
    ).all()
    
    # If user is a Co-PI with budget authority, also find steps requiring 'PI' role 
    # but ONLY for the grants they have authority over.
    if co_pi_grant_ids:
        pi_steps = ApprovalStep.query.join(ApprovalWorkflow).filter(
            ApprovalStep.status == 'active',
            ApprovalStep.role_required == 'PI',
            ApprovalWorkflow.grant_id.in_(co_pi_grant_ids)
        ).all()
        pending_steps.extend(pi_steps)
    
    results = []
    for step in pending_steps:
        workflow = step.workflow
        # Enrich with item data
        item_data = {}
        if workflow.item_type == 'VIREMENT':
            v = BudgetVirement.query.get(workflow.item_id)
            if v:
                item_data = {
                    'title': f"Budget Virement: {v.amount} from {v.from_category.name} to {v.to_category.name}",
                    'requester': v.created_by.name if v.created_by else "Unknown",
                    'amount': v.amount,
                    'justification': v.justification,
                    'grant_title': v.grant.title if v.grant else "Unknown",
                    'category': 'Virement'
                }
        elif workflow.item_type == 'PRIOR_APPROVAL':
            pa = PriorApprovalRequest.query.get(workflow.item_id)
            if pa:
                item_data = {
                    'title': f"Prior Approval: {pa.request_type} - {pa.category}",
                    'requester': pa.requester.name if pa.requester else "Unknown",
                    'amount': pa.amount,
                    'justification': pa.justification,
                    'grant_title': pa.grant.title if pa.grant else "Unknown",
                    'category': pa.request_type
                }
        elif workflow.item_type == 'EXPENSE':
            e = ExpenseClaim.query.get(workflow.item_id)
            if e:
                item_data = {
                    'title': f"Expense Claim: {e.category} - {e.amount}",
                    'requester': e.submitter.name if e.submitter else "Unknown",
                    'amount': e.amount,
                    'justification': e.description,
                    'grant_title': e.grant.title if e.grant else "Unknown",
                    'category': 'Expense',
                    'receipt_filename': e.receipt_filename
                }
        
        results.append({
            'workflow_id': workflow.id,
            'step_id': step.id,
            'item_type': workflow.item_type,
            'item_id': workflow.item_id,
            'item_data': item_data,
            'order': step.order,
            'created_at': workflow.created_at.isoformat()
        })
        
    return jsonify(results), 200

@approvals_bp.route('/approvals/<int:workflow_id>/action', methods=['POST'])
def take_approval_action(workflow_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    data = request.json
    action = data.get('action') # APPROVE | REJECT
    comment = data.get('comment')
    
    if action not in ['APPROVE', 'REJECT']:
        return jsonify({'error': 'Invalid action'}), 400
        
    try:
        # Determine effective role for this workflow
        effective_role = user.role.upper()
        
        # Check if user is acting as a Co-PI for this grant
        workflow_obj = ApprovalWorkflow.query.get(workflow_id)
        if workflow_obj and workflow_obj.grant_id and effective_role == 'TEAM':
            from models import GrantTeam
            co_pi_entry = GrantTeam.query.filter_by(
                user_id=user.id,
                grant_id=workflow_obj.grant_id,
                role='Co-PI',
                budget_authority=True,
                status='active'
            ).first()
            if co_pi_entry:
                effective_role = 'PI' # Elevate role to PI for this specific workflow context

        workflow = workflow_service.process_action(
            workflow_id=workflow_id,
            user_id=user.id,
            role=effective_role,
            action=action,
            comment=comment
        )
        
        # --- Handle Completion Callbacks ---
        if workflow.status == 'completed':
            if workflow.item_type == 'VIREMENT':
                # Final execution: Move funds and release encumbrance
                virement_service.approve_virement(workflow.item_id, user.id)
            elif workflow.item_type == 'PRIOR_APPROVAL':
                # Mark request as approved
                prior_approval_service.sync_with_workflow(workflow.item_id, 'completed')
            elif workflow.item_type == 'EXPENSE':
                e = ExpenseClaim.query.get(workflow.item_id)
                if e:
                    e.status = 'pending' # Move to Finance queue
                    e.approved_at = datetime.utcnow()
                    db.session.commit()
        
        elif workflow.status == 'rejected':
             if workflow.item_type == 'VIREMENT':
                # Release encumbrance
                virement_service.reject_virement(workflow.item_id, user.id, comment)
             elif workflow.item_type == 'PRIOR_APPROVAL':
                # Mark request as rejected
                prior_approval_service.sync_with_workflow(workflow.item_id, 'rejected')
             elif workflow.item_type == 'EXPENSE':
                e = ExpenseClaim.query.get(workflow.item_id)
                if e:
                    e.status = 'rejected'
                    db.session.commit()

        return jsonify({'message': f'Action {action} processed' , 'workflow_status': workflow.status}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
         return jsonify({'error': 'System error', 'details': str(e)}), 500
