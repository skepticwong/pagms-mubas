# backend/routes/expenses.py
from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
from models import db, ExpenseClaim, Grant, User, BudgetCategory, AuditLog, PriorApprovalRequest, RuleEvaluation
from services.grant_service import GrantService
from services.rule_service import RuleService
from services.effort_service import EffortService
from services.audit_service import AuditService
from services.health_score_service import HealthScoreService

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses', methods=['GET'])
def get_expenses():
    """
    Get expense claims.
    - PI: All claims for their grants.
    - Team: Their own submitted claims.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        if user.role in ['Finance', 'RSU']:
            # Finance/RSU see all claims
            claims = ExpenseClaim.query
        elif user.role == 'PI':
            # Get all grants owned by PI
            grants = Grant.query.filter_by(pi_id=user_id).all()
            grant_ids = [g.id for g in grants]
            
            # Also get grants where the user is a Co-PI
            from models import GrantTeam
            co_pi_entries = GrantTeam.query.filter_by(user_id=user_id, role='Co-PI', status='active').all()
            co_pi_grant_ids = [entry.grant_id for entry in co_pi_entries]
            
            all_grant_ids = list(set(grant_ids + co_pi_grant_ids))
            claims = ExpenseClaim.query.filter(ExpenseClaim.grant_id.in_(all_grant_ids))
        elif user.role == 'Team':
            # Check if they are a Co-PI on any grants (they might have system role 'Team')
            from models import GrantTeam
            co_pi_entries = GrantTeam.query.filter_by(user_id=user_id, role='Co-PI', status='active').all()
            if co_pi_entries:
                co_pi_grant_ids = [entry.grant_id for entry in co_pi_entries]
                # See their own claims OR all claims for grants where they are Co-PI
                claims = ExpenseClaim.query.filter(
                    (ExpenseClaim.submitted_by == user_id) | 
                    (ExpenseClaim.grant_id.in_(co_pi_grant_ids))
                )
            else:
                # Team sees only THEIR OWN claims
                claims = ExpenseClaim.query.filter_by(submitted_by=user_id)
        else:
            return jsonify({'expenses': []})

        claims = claims.order_by(ExpenseClaim.submitted_at.desc()).all()

        results = []
        for claim in claims:
            grant = Grant.query.get(claim.grant_id)
            submitter = User.query.get(claim.submitted_by)
            results.append({
                'id': claim.id,
                'grant_id': claim.grant_id,
                'grant_title': grant.title if grant else 'Unknown',
                'submitted_by_name': submitter.name if submitter else 'Unknown',
                'category': claim.category,
                'amount': claim.amount,
                'currency': claim.currency,
                'status': claim.status,
                'expense_date': claim.expense_date.isoformat() if claim.expense_date else None,
                'description': claim.description,
                'receipt_filename': claim.receipt_filename,
                'payment_method': claim.payment_method,
                'submitted_at': claim.submitted_at.isoformat() if claim.submitted_at else None
            })

        return jsonify({'expenses': results}), 200

    except Exception as e:
        print(f"Error fetching expenses: {str(e)}")
        return jsonify({'error': 'Failed to fetch expenses', 'details': str(e)}), 500

@expenses_bp.route('/expenses', methods=['POST'])
def submit_expense():
    """
    Submit a new expense claim.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        # 1. Extract and validate basic fields
        grant_id = request.form.get('grant_id')
        category_name = request.form.get('category')
        amount = request.form.get('amount')
        expense_date_str = request.form.get('expense_date')
        description = request.form.get('description')
        payment_method = request.form.get('payment_method')

        if not all([grant_id, category_name, amount, expense_date_str]):
            return jsonify({'error': 'Missing required fields (grant_id, category, amount, expense_date)'}), 400

        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
            
        # Permission check
        is_authorized = False
        if user.role == 'PI' and grant.pi_id == user_id:
            is_authorized = True
        elif user.role == 'Team':
            from models import GrantTeam
            entry = GrantTeam.query.filter_by(grant_id=grant_id, user_id=user_id).first()
            if entry:
                is_authorized = True
        
        if not is_authorized:
            return jsonify({'error': 'You do not have permission to submit expenses for this grant'}), 403

        # 1.5 Effort Certification Lock (Audit-Proof Enforcement Gate)
        is_locked, lock_msg, severity = EffortService.check_spending_lock(grant_id)
        if is_locked:
            return jsonify({
                'error': lock_msg,
                'type': 'COMPLIANCE_LOCK',
                'severity': severity
            }), 403

        # 1.6 Ethics Compliance Lock (New)
        if grant.ethics_required and grant.ethics_status in ['PENDING_ETHICS', 'SUSPENDED_ETHICS']:
            status_display = "pending RSU verification" if grant.ethics_status == 'PENDING_ETHICS' else "suspended due to expiry"
            return jsonify({
                'error': f'Ethics Compliance Lock: This grant is currently {status_display}. Financial modules are locked.',
                'type': 'ETHICS_LOCK',
                'ethics_status': grant.ethics_status
            }), 403

        # 2. Budget Validation
        amount = float(amount)
        
        # 2.1 Tranche Disbursement Check (Spending Gating)
        total_grant_spent = sum((cat.spent or 0.0) for cat in grant.categories)
        if total_grant_spent + amount > grant.disbursed_funds:
            return jsonify({
                'error': 'Insufficient disbursed funds. Please wait for the next tranche release.',
                'disbursed_funds': grant.disbursed_funds,
                'total_spent': total_grant_spent,
                'available_to_spend': grant.disbursed_funds - total_grant_spent
            }), 403

        category = BudgetCategory.query.filter_by(grant_id=grant_id, name=category_name).first()
        if not category:
            return jsonify({'error': f'Budget category "{category_name}" not found for this grant'}), 400

        remaining = category.allocated - category.spent
        if amount > remaining:
            return jsonify({
                'error': f'Insufficient budget. Available in "{category_name}": {remaining}',
                'available': remaining
            }), 400

        # 3. Handle File Upload
        receipt_file = request.files.get('receipt')
        receipt_filename = None
        if receipt_file:
            from services.grant_service import GrantService
            receipt_filename = GrantService._save_file(receipt_file, 'receipts')

        # 4. Prior Approval Linking (Proactive Authorization)
        prior_approval_id = request.form.get('prior_approval_id')
        pre_approved = False
        if prior_approval_id:
            pa_req = PriorApprovalRequest.query.get(prior_approval_id)
            if pa_req and pa_req.status == 'approved' and pa_req.grant_id == int(grant_id):
                # Basic check: amount shouldn't exceed approved amount by more than 5% (buffer)
                if amount <= (pa_req.amount * 1.05):
                    pre_approved = True

        # 5. Rule Engine Evaluation (Compliance Check 2.0)
        expense_context = {
            'category': category_name,
            'amount': amount,
            'description': description,
            'date': expense_date_str,
            'action_type': 'EXPENSE'
        }
        rule_result = RuleService.evaluate_action('EXPENSE', expense_context, grant_id)
        
        final_status = 'pending'
        if rule_result['outcome'] == 'BLOCK':
            reasons = "; ".join([r['guidance_text'] for r in rule_result['triggered_rules']])
            
            # Log BLOCK in Audit Trail
            AuditService.log_action(
                user_id=user_id,
                action='EXPENSE_BLOCKED',
                entity_type='EXPENSE',
                entity_id=0,
                details={'reason': reasons, 'context': expense_context}
            )
            
            # Recalculate health (Penalty for block)
            HealthScoreService.calculate_score(grant_id)

            return jsonify({
                'error': 'Compliance Block: This expense is unallowable according to funder rules.',
                'reasons': reasons,
                'triggered_rules': rule_result['triggered_rules']
            }), 403
        
        if rule_result['outcome'] == 'PRIOR_APPROVAL' and not pre_approved:
            final_status = 'awaiting_prior_approval'
        
        # 6. Create Expense Claim
        expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
        
        claim = ExpenseClaim(
            grant_id=grant_id,
            submitted_by=user_id,
            category=category_name,
            amount=amount,
            currency=grant.currency,
            expense_date=expense_date,
            description=description,
            receipt_filename=receipt_filename,
            payment_method=payment_method,
            status=final_status,
            prior_approval_id=prior_approval_id if pre_approved else None
        )
        db.session.add(claim)
        db.session.flush() # Get claim.id

        # 6. Handle Prior Approval Request if needed
        if rule_result['outcome'] == 'PRIOR_APPROVAL':
            # Create a combined request for all triggered rules that require approval
            # For simplicity, we link all triggered evaluations to this one request 
            # or just use the first one as representative
            eval_ids = rule_result.get('evaluation_ids', [])
            
            pa_request = PriorApprovalRequest(
                grant_id=grant_id,
                requester_id=user_id,
                request_type='EXPENSE',
                target_id=claim.id,
                rule_evaluation_id=eval_ids[0] if eval_ids else None,
                status='pending',
                justification=request.form.get('prior_approval_justification', 'Compliance triggered prior approval.')
            )
            db.session.add(pa_request)
        
        # 7. Forensic Audit & Health Update
        AuditService.log_action(
            user_id=user_id,
            action='EXPENSE_SUBMITTED',
            entity_type='EXPENSE',
            entity_id=claim.id,
            details={
                'amount': amount,
                'category': category_name,
                'outcome': rule_result["outcome"]
            }
        )
        
        # Update health for warnings or prior approvals
        if rule_result['outcome'] in ['WARN', 'PRIOR_APPROVAL']:
            HealthScoreService.calculate_score(grant_id)
        
        db.session.commit()
        
        response_data = {
            'message': 'Expense submitted successfully' if final_status == 'pending' else 'Expense submitted and awaiting prior approval',
            'claim': claim.to_dict(),
            'compliance_outcome': rule_result['outcome'],
            'triggered_rules': rule_result['triggered_rules']
        }
        
        return jsonify(response_data), 201

    except ValueError:
        return jsonify({'error': 'Invalid amount or date format'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Expense submission error: {str(e)}")
        return jsonify({'error': 'Failed to submit expense', 'details': str(e)}), 500


@expenses_bp.route('/grants/<int:grant_id>/budget-categories', methods=['GET'])
def get_budget_categories(grant_id):
    """
    Get budget categories for a grant with remaining balances.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404

        # Authorization check
        is_authorized = False
        if user.role == 'PI' and grant.pi_id == user_id:
            is_authorized = True
        else:
            from models import GrantTeam
            entry = GrantTeam.query.filter_by(grant_id=grant_id, user_id=user_id, status='active').first()
            if entry and (entry.role == 'Co-PI' or user.role == 'Team' or user.role == 'Finance' or user.role == 'RSU'):
                is_authorized = True

        if not is_authorized:
            return jsonify({'error': 'You do not have permission to view this grant'}), 403

        categories = BudgetCategory.query.filter_by(grant_id=grant_id).all()
        
        results = []
        for cat in categories:
            results.append({
                'id': cat.id,
                'name': cat.name,
                'allocated': cat.allocated,
                'spent': cat.spent,
                'remaining': cat.allocated - cat.spent
            })

        return jsonify({'categories': results}), 200

    except Exception as e:
        print(f"Error fetching budget categories: {str(e)}")
        return jsonify({'error': 'Failed to fetch budget categories', 'details': str(e)}), 500


@expenses_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """
    Update a pending expense claim.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        expense = ExpenseClaim.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404

        # Only allow editing pending expenses
        if expense.status != 'pending':
            return jsonify({'error': 'Can only edit pending expenses'}), 400

        # Authorization check
        grant = Grant.query.get(expense.grant_id)
        is_authorized = False
        if user.role == 'PI' and grant.pi_id == user_id:
            is_authorized = True
        elif expense.submitted_by == user_id:
            is_authorized = True

        if not is_authorized:
            return jsonify({'error': 'You do not have permission to edit this expense'}), 403

        # 1.6 Ethics Compliance Lock (New)
        if grant.ethics_required and grant.ethics_status in ['PENDING_ETHICS', 'SUSPENDED_ETHICS']:
            status_display = "pending RSU verification" if grant.ethics_status == 'PENDING_ETHICS' else "suspended due to expiry"
            return jsonify({
                'error': f'Ethics Compliance Lock: This grant is currently {status_display}. Modification of expenses is locked.',
                'type': 'ETHICS_LOCK',
                'ethics_status': grant.ethics_status
            }), 403

        # Update fields
        category_name = request.form.get('category')
        amount = request.form.get('amount')
        expense_date_str = request.form.get('expense_date')
        description = request.form.get('description')

        if category_name:
            # Validate budget if category or amount changed
            new_amount = float(amount) if amount else expense.amount
            category = BudgetCategory.query.filter_by(grant_id=expense.grant_id, name=category_name).first()
            if not category:
                return jsonify({'error': f'Budget category "{category_name}" not found'}), 400

            # Calculate remaining budget (excluding current expense)
            remaining = category.allocated - category.spent
            if category_name == expense.category:
                remaining += expense.amount  # Add back current expense amount

            if new_amount > remaining:
                return jsonify({
                    'error': f'Insufficient budget. Available in "{category_name}": {remaining}',
                    'available': remaining
                }), 400

            expense.category = category_name

        if amount:
            expense.amount = float(amount)

        if expense_date_str:
            expense.expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()

        if description:
            expense.description = description

        # Handle receipt file update
        receipt_file = request.files.get('receipt')
        if receipt_file:
            from services.grant_service import GrantService
            expense.receipt_filename = GrantService._save_file(receipt_file, 'receipts')

        # Re-run Rule Engine Evaluation if amount or category changed
        rule_outcome = 'PASS'
        if category_name or amount:
            expense_context = {
                'category': expense.category,
                'amount': expense.amount,
                'description': expense.description,
                'date': expense.expense_date.isoformat() if expense.expense_date else ""
            }
            rule_result = RuleService.evaluate_expense(expense_context, expense.grant_id)
            rule_outcome = rule_result['outcome']
            
            if rule_outcome == 'BLOCK':
                db.session.rollback()
                reasons = "; ".join([r['guidance_text'] for r in rule_result['triggered_rules']])
                return jsonify({
                    'error': 'Compliance Block: Updated expense is unallowable.',
                    'reasons': reasons,
                    'triggered_rules': rule_result['triggered_rules']
                }), 403
            
            if rule_outcome == 'PRIOR_APPROVAL':
                expense.status = 'awaiting_prior_approval'
                # Check for existing pending PA request or create new one
                pa_request = PriorApprovalRequest.query.filter_by(
                    request_type='EXPENSE', 
                    target_id=expense.id,
                    status='pending'
                ).first()
                
                if not pa_request:
                    eval_ids = rule_result.get('evaluation_ids', [])
                    pa_request = PriorApprovalRequest(
                        grant_id=expense.grant_id,
                        requester_id=user_id,
                        request_type='EXPENSE',
                        target_id=expense.id,
                        rule_evaluation_id=eval_ids[0] if eval_ids else None,
                        status='pending',
                        justification='Updated expense triggered prior approval.'
                    )
                    db.session.add(pa_request)
            else:
                # If it was awaiting_prior_approval but now PASS/WARN, we might want to reset it?
                # For now let's just allow it to stay as pending if it passes.
                if expense.status == 'awaiting_prior_approval':
                    expense.status = 'pending'

        db.session.commit()

        return jsonify({
            'message': 'Expense updated successfully', 
            'claim': expense.to_dict(),
            'compliance_outcome': rule_outcome
        }), 200

    except ValueError:
        return jsonify({'error': 'Invalid amount or date format'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating expense: {str(e)}")
        return jsonify({'error': 'Failed to update expense', 'details': str(e)}), 500


@expenses_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """
    Delete a pending expense claim.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        expense = ExpenseClaim.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404

        # Only allow deleting pending expenses
        if expense.status != 'pending':
            return jsonify({'error': 'Can only delete pending expenses'}), 400

        # Authorization check
        grant = Grant.query.get(expense.grant_id)
        is_authorized = False
        if user.role == 'PI' and grant.pi_id == user_id:
            is_authorized = True
        elif expense.submitted_by == user_id:
            is_authorized = True

        if not is_authorized:
            return jsonify({'error': 'You do not have permission to delete this expense'}), 403

        db.session.delete(expense)
        db.session.commit()

        return jsonify({'message': 'Expense deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting expense: {str(e)}")
        return jsonify({'error': 'Failed to delete expense', 'details': str(e)}), 500
