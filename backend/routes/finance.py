# backend/routes/finance.py
from flask import Blueprint, jsonify, session, request
from models import db, Grant, ExpenseClaim, BudgetCategory, User, Milestone, AuditLog, Tranche
from datetime import datetime, timedelta
from sqlalchemy import func, extract

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/finance/dashboard', methods=['GET'])
def get_finance_dashboard():
    """
    Finance dashboard data for Finance role users.
    Returns: headline metrics, disbursement queue, exceptions, alerts, and insights.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    try:
        # ===== HEADLINE METRICS =====
        # Total Portfolio: Sum of all active grants
        total_portfolio = db.session.query(func.sum(Grant.total_budget))\
            .filter(Grant.status == 'active').scalar() or 0
        
        # Disbursed: Sum of approved expense claims
        disbursed = db.session.query(func.sum(ExpenseClaim.amount))\
            .filter(ExpenseClaim.status == 'approved').scalar() or 0
        
        # Commitments: Sum of pending expense claims
        commitments = db.session.query(func.sum(ExpenseClaim.amount))\
            .filter(ExpenseClaim.status == 'pending').scalar() or 0
        
        # Pending Claims Count
        pending_claims = db.session.query(func.count(ExpenseClaim.id))\
            .filter(ExpenseClaim.status == 'pending').scalar() or 0
        
        # Variances: (Spent - Allocated) / Allocated
        budget_stats = db.session.query(
            func.sum(BudgetCategory.spent),
            func.sum(BudgetCategory.allocated)
        ).first()
        
        total_spent = budget_stats[0] or 0
        total_allocated = budget_stats[1] or 1  # Avoid division by zero
        variances = (total_spent - total_allocated) / total_allocated if total_allocated > 0 else 0

        headline = {
            'totalPortfolio': round(total_portfolio / 1_000_000, 2),  # Convert to millions
            'disbursed': round(disbursed / 1_000_000, 2),
            'commitments': round(commitments / 1_000_000, 2),
            'pendingClaims': pending_claims,
            'variances': round(variances, 2)
        }

        # ===== DISBURSEMENT QUEUE =====
        # Get pending expense claims with grant details
        pending_expenses = db.session.query(
            ExpenseClaim,
            Grant.title.label('grant_title')
        ).join(Grant, ExpenseClaim.grant_id == Grant.id)\
            .filter(ExpenseClaim.status == 'pending')\
            .order_by(ExpenseClaim.submitted_at.asc())\
            .limit(10).all()

        disbursement_queue = []
        for expense, grant_title in pending_expenses:
            age_days = (datetime.utcnow() - expense.submitted_at).days if expense.submitted_at else 0
            disbursement_queue.append({
                'grant': grant_title,
                'amount': expense.amount,
                'stage': 'Pending Approval' if age_days < 5 else 'Awaiting Review',
                'age': f"{age_days} days",
                'grant_id': expense.grant_id,
                'expense_id': expense.id
            })

        # ===== READY DISBURSEMENTS =====
        active_grants = Grant.query.filter_by(status='active').all()
        for grant in active_grants:
            if grant.disbursement_type == 'single':
                # Show if no funds disbursed yet
                if (grant.disbursed_funds or 0) == 0:
                    disbursement_queue.append({
                        'grant': grant.title,
                        'amount': grant.total_budget,
                        'stage': 'SINGLE_PAYMENT_READY',
                        'age': 'Ready',
                        'grant_id': grant.id,
                        'is_disbursement': True,
                        'type': 'single'
                    })
            elif grant.disbursement_type == 'tranches':
                # Check manual tranches
                for tr in grant.tranches:
                    if tr.status == 'pending' and tr.expected_date <= datetime.utcnow().date():
                        disbursement_queue.append({
                            'grant': grant.title,
                            'amount': tr.amount,
                            'stage': f'TRANCHE DUE ({tr.expected_date})',
                            'age': 'Ready',
                            'grant_id': grant.id,
                            'tranche_id': tr.id,
                            'is_disbursement': True,
                            'type': 'tranche'
                        })
            elif grant.disbursement_type == 'milestone_based':
                # Check milestones that are COMPLETED but not yet RELEASED
                for m in grant.milestones_list:
                    if m.status == 'COMPLETED' and m.release_status == 'pending' and (m.funding_amount or 0) > 0:
                        disbursement_queue.append({
                            'grant': grant.title,
                            'amount': m.funding_amount,
                            'stage': f'MILESTONE_COMPLETED: {m.title}',
                            'age': 'Ready',
                            'grant_id': grant.id,
                            'milestone_id': m.id,
                            'is_disbursement': True,
                            'type': 'milestone'
                        })

        # ===== EXCEPTIONS =====
        exceptions = []
        
        # Find budget overruns (spent > 90% of allocated)
        overruns = db.session.query(
            BudgetCategory,
            Grant.title.label('grant_title')
        ).join(Grant, BudgetCategory.grant_id == Grant.id)\
            .filter(BudgetCategory.spent > BudgetCategory.allocated * 0.9)\
            .limit(5).all()
        
        for budget, grant_title in overruns:
            percentage = (budget.spent / budget.allocated * 100) if budget.allocated > 0 else 0
            exceptions.append({
                'grant': grant_title,
                'issue': f"{budget.name} budget at {percentage:.0f}%",
                'action': 'Review spending and reallocate if needed',
                'owner': 'Finance Ops'
            })
        
        # Find delayed approvals (pending > 30 days)
        delayed = db.session.query(
            ExpenseClaim,
            Grant.title.label('grant_title')
        ).join(Grant, ExpenseClaim.grant_id == Grant.id)\
            .filter(ExpenseClaim.status == 'pending')\
            .filter(ExpenseClaim.ageing_days > 30)\
            .limit(5).all()
        
        for expense, grant_title in delayed:
            exceptions.append({
                'grant': grant_title,
                'issue': f"Delayed approval ({expense.ageing_days} days)",
                'action': 'Escalate to PI',
                'owner': 'Compliance'
            })

        # ===== ALERTS =====
        alerts = []
        
        # High-value expense claims (> $5000)
        high_value_count = db.session.query(func.count(ExpenseClaim.id))\
            .filter(ExpenseClaim.status == 'pending')\
            .filter(ExpenseClaim.amount > 5000).scalar() or 0
        
        if high_value_count > 0:
            alerts.append(f"{high_value_count} expense claims exceed policy limits (> $5K)")
        
        # Blocked disbursements (very old pending claims)
        blocked_count = db.session.query(func.count(ExpenseClaim.id))\
            .filter(ExpenseClaim.status == 'pending')\
            .filter(ExpenseClaim.ageing_days > 45).scalar() or 0
        
        if blocked_count > 0:
            alerts.append(f"{blocked_count} grant disbursement(s) blocked pending audit clarification")

        # ===== INSIGHTS =====
        # Cash Coverage: Months of runway (simplified calculation)
        monthly_burn = disbursed / 12 if disbursed > 0 else 1
        cash_coverage = (total_portfolio - disbursed) / monthly_burn if monthly_burn > 0 else 0
        
        # FX Exposure: Percentage of portfolio in foreign currency (simplified)
        fx_exposure = 0.28  # Placeholder - would need currency tracking
        
        # Overdue Invoices: Pending expenses > 30 days
        overdue_invoices = db.session.query(func.count(ExpenseClaim.id))\
            .filter(ExpenseClaim.status == 'pending')\
            .filter(ExpenseClaim.ageing_days > 30).scalar() or 0
        
        # Avg Processing Days: Average time from submission to approval
        avg_processing = db.session.query(
            func.avg(
                func.julianday(ExpenseClaim.approved_at) - 
                func.julianday(ExpenseClaim.submitted_at)
            )
        ).filter(ExpenseClaim.status == 'approved')\
            .filter(ExpenseClaim.approved_at.isnot(None)).scalar() or 0

        insights = {
            'cashCoverage': round(cash_coverage, 1),
            'fxExposure': round(fx_exposure, 2),
            'overdueInvoices': overdue_invoices,
            'avgProcessingDays': round(avg_processing, 1)
        }

        return jsonify({
            'headline': headline,
            'disbursementQueue': disbursement_queue,
            'exceptions': exceptions,
            'alerts': alerts,
            'insights': insights
        }), 200

    except Exception as e:
        print(f"Error fetching finance dashboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch finance dashboard', 'details': str(e)}), 500


@finance_bp.route('/finance/burn-rate', methods=['GET'])
def get_burn_rate():
    """
    Quarterly burn rate: actual vs forecast spending.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    try:
        # Get current year
        current_year = datetime.utcnow().year
        
        # Calculate quarterly spending
        burn_rate = []
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        quarter_months = [(1, 3), (4, 6), (7, 9), (10, 12)]
        
        # Get total budget for the year
        total_budget = db.session.query(func.sum(BudgetCategory.allocated)).scalar() or 1
        
        for i, (start_month, end_month) in enumerate(quarter_months):
            # Calculate actual spending for this quarter
            actual_spent = db.session.query(func.sum(ExpenseClaim.amount))\
                .filter(ExpenseClaim.status == 'approved')\
                .filter(extract('year', ExpenseClaim.approved_at) == current_year)\
                .filter(extract('month', ExpenseClaim.approved_at) >= start_month)\
                .filter(extract('month', ExpenseClaim.approved_at) <= end_month)\
                .scalar() or 0
            
            # Calculate forecast (25% per quarter as baseline)
            forecast = 0.25
            actual = actual_spent / total_budget if total_budget > 0 else 0
            
            burn_rate.append({
                'label': quarters[i],
                'actual': round(actual, 2),
                'forecast': forecast
            })
        
        return jsonify({'burnRate': burn_rate}), 200

    except Exception as e:
        print(f"Error fetching burn rate: {str(e)}")
        return jsonify({'error': 'Failed to fetch burn rate', 'details': str(e)}), 500


@finance_bp.route('/finance/fx-rates', methods=['GET'])
def get_fx_rates():
    """
    Current FX rates for major currencies.
    Note: This returns static rates. In production, integrate with RBM API or similar.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    # Static rates - in production, fetch from external API
    rates = {
        'usd': {'buying': 1705, 'selling': 1722},
        'eur': {'buying': 1850, 'selling': 1870},
        'gbp': {'buying': 2125, 'selling': 2150}
    }

    return jsonify({'rates': rates}), 200


@finance_bp.route('/finance/deadlines', methods=['GET'])
def get_deadlines():
    """
    Upcoming reporting deadlines from milestones.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    try:
        # Get upcoming milestones (next 90 days)
        upcoming_date = datetime.utcnow().date() + timedelta(days=90)
        
        milestones = db.session.query(
            Milestone.due_date,
            Milestone.reporting_period,
            func.count(Milestone.grant_id).label('grant_count')
        ).filter(Milestone.due_date <= upcoming_date)\
            .filter(Milestone.due_date >= datetime.utcnow().date())\
            .filter(Milestone.status != 'completed')\
            .group_by(Milestone.due_date, Milestone.reporting_period)\
            .order_by(Milestone.due_date.asc())\
            .limit(10).all()

        deadlines = []
        for milestone in milestones:
            deadlines.append({
                'date': milestone.due_date.strftime('%d %b'),
                'label': milestone.reporting_period or 'Financial Report',
                'grants': milestone.grant_count
            })

        return jsonify({'deadlines': deadlines}), 200

    except Exception as e:
        print(f"Error fetching deadlines: {str(e)}")
        return jsonify({'error': 'Failed to fetch deadlines', 'details': str(e)}), 500


@finance_bp.route('/finance/pending-expenses', methods=['GET'])
def get_pending_expenses():
    """
    Get all pending expense claims with detailed information for Finance approval.
    Includes: claim details, grant info, PI info, attachments, ageing, and KPIs.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    try:
        # Get all pending expense claims with grant and PI details
        pending_claims = db.session.query(
            ExpenseClaim,
            Grant.title.label('grant_title'),
            User.name.label('pi_name')
        ).join(Grant, ExpenseClaim.grant_id == Grant.id)\
            .join(User, Grant.pi_id == User.id)\
            .filter(ExpenseClaim.status == 'pending')\
            .order_by(ExpenseClaim.submitted_at.asc())\
            .all()

        claims_list = []
        for expense, grant_title, pi_name in pending_claims:
            # Calculate ageing days
            age_days = (datetime.utcnow() - expense.submitted_at).days if expense.submitted_at else 0
            
            # Determine status based on ageing
            if age_days > 10:
                status = 'Compliance Review'
            elif age_days > 5:
                status = 'PI Clarification'
            else:
                status = 'Awaiting Treasury'
            
            # Count attachments (if receipt_filename exists, count as 1, can be extended)
            attachments = 1 if expense.receipt_filename else 0
            
            # Convert to MWK (using approximate rate of 1705 MWK per USD)
            amount_mwk = expense.amount * 1705
            
            claims_list.append({
                'id': f'EXP-{expense.id}',
                'grant': grant_title,
                'pi': pi_name,
                'category': expense.category,
                'amountUSD': expense.amount,
                'amountMWK': amount_mwk,
                'submitted': expense.submitted_at.isoformat() if expense.submitted_at else None,
                'ageingDays': age_days,
                'status': status,
                'attachments': attachments,
                'description': expense.description,
                'expense_id': expense.id,
                'grant_id': expense.grant_id
            })

        # Calculate KPIs
        total_claims = len(claims_list)
        claims_over_7_days = len([c for c in claims_list if c['ageingDays'] > 7])
        
        # Average turnaround time
        avg_processing = db.session.query(
            func.avg(
                func.julianday(ExpenseClaim.approved_at) - 
                func.julianday(ExpenseClaim.submitted_at)
            )
        ).filter(ExpenseClaim.status == 'approved')\
            .filter(ExpenseClaim.approved_at.isnot(None)).scalar() or 0
        
        # Total USD exposure (sum of pending claims)
        usd_exposure = sum([c['amountUSD'] for c in claims_list])
        
        # Average ageing
        avg_ageing = sum([c['ageingDays'] for c in claims_list]) / total_claims if total_claims > 0 else 0
        
        # Policy exceptions (high-value claims > $5000)
        policy_exceptions = len([c for c in claims_list if c['amountUSD'] > 5000])

        kpis = {
            'avgTurnaround': round(avg_processing, 1),
            'claimsOver7Days': claims_over_7_days,
            'usdExposure': round(usd_exposure, 2),
            'policyExceptions': policy_exceptions,
            'avgAgeing': round(avg_ageing, 1)
        }

        return jsonify({
            'claims': claims_list,
            'kpis': kpis
        }), 200

    except Exception as e:
        print(f"Error fetching pending expenses: {str(e)}")
        return jsonify({'error': 'Failed to fetch pending expenses', 'details': str(e)}), 500


@finance_bp.route('/finance/expenses/<int:expense_id>/approve', methods=['POST'])
def approve_expense(expense_id):
    """
    Approve an expense claim.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    try:
        expense = ExpenseClaim.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense claim not found'}), 404

        if expense.status != 'pending':
            return jsonify({'error': 'Expense claim is not pending'}), 400

        # Update expense status
        expense.status = 'approved'
        expense.approved_at = datetime.utcnow()
        
        # Update budget category spent amount
        grant = Grant.query.get(expense.grant_id)
        if grant:
            budget_category = BudgetCategory.query.filter_by(
                grant_id=grant.id,
                name=expense.category
            ).first()
            
            if budget_category:
                budget_category.spent += expense.amount

        db.session.commit()

        return jsonify({'message': 'Expense approved successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error approving expense: {str(e)}")
        return jsonify({'error': 'Failed to approve expense', 'details': str(e)}), 500


@finance_bp.route('/finance/expenses/<int:expense_id>/reject', methods=['POST'])
def reject_expense(expense_id):
    """
    Reject/escalate an expense claim.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'Finance':
        return jsonify({'error': 'Access denied. Finance role required.'}), 403

    try:
        expense = ExpenseClaim.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense claim not found'}), 404

        if expense.status != 'pending':
            return jsonify({'error': 'Expense claim is not pending'}), 400

        # Update expense status
        expense.status = 'rejected'
        db.session.commit()

        return jsonify({'message': 'Expense rejected successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting expense: {str(e)}")
        return jsonify({'error': 'Failed to reject expense', 'details': str(e)}), 500

@finance_bp.route('/finance/release-disbursement', methods=['POST'])
def release_disbursement():
    """
    Release funds for a grant based on the disbursement model.
    """
    user_id = session.get('user_id')
    if not user_id: return jsonify({'error': 'Not authenticated'}), 401
    user = User.query.get(user_id)
    if not user or user.role != 'Finance': return jsonify({'error': 'Access denied'}), 403

    data = request.json
    grant_id = data.get('grant_id')
    release_type = data.get('type') # 'single', 'tranche', 'milestone'
    item_id = data.get('item_id') # Tranche.id or Milestone.id

    if not grant_id or not release_type:
        return jsonify({'error': 'grant_id and type required'}), 400

    try:
        grant = Grant.query.get_or_404(grant_id)
        amount_released = 0
        detail_text = ""

        if release_type == 'single':
            amount_released = grant.total_budget
            grant.disbursed_funds = amount_released
            detail_text = "Single payment full disbursement"
        
        elif release_type == 'tranche':
            tr = Tranche.query.get_or_404(item_id)
            if tr.grant_id != grant.id: return jsonify({'error': 'Invalid tranche'}), 400
            tr.status = 'received'
            tr.actual_received_date = datetime.utcnow().date()
            amount_released = tr.amount
            grant.disbursed_funds += amount_released
            detail_text = f"Manual Tranche (Due {tr.expected_date}) released"

        elif release_type == 'milestone':
            m = Milestone.query.get_or_404(item_id)
            if m.grant_id != grant.id: return jsonify({'error': 'Invalid milestone'}), 400
            if m.status != 'COMPLETED': return jsonify({'error': 'Milestone not completed'}), 400
            m.release_status = 'released'
            amount_released = m.funding_amount
            grant.disbursed_funds += amount_released
            detail_text = f"Milestone '{m.title}' release"
        
        else:
            return jsonify({'error': 'Invalid release type'}), 400

        # Log Audit
        db.session.add(AuditLog(
            user_id=user_id,
            action='disbursement_released',
            resource_type='grant',
            resource_id=grant.id,
            details=f'{detail_text} ({amount_released} {grant.currency}) released by Finance'
        ))
        
        db.session.commit()
        
        return jsonify({
            'message': 'Disbursement successfully released.',
            'amount_released': amount_released,
            'total_disbursed': grant.disbursed_funds
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
