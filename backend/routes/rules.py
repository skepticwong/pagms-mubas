from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from models import db, Rule, FunderProfile, RuleEvaluation, User, PriorApprovalRequest, RuleExemption, ExpenseClaim, GrantTeam, Grant
from services.rule_service import RuleService
from services.enhanced_rule_service import EnhancedRuleService
from services.rule_enforcement_service import RuleEnforcementService
from middleware import token_required, rsu_required

rules_bp = Blueprint('rules', __name__)

@rules_bp.route('/rule-profiles/active', methods=['GET'])
@token_required
def get_active_profiles(user):
    funder_id = request.args.get('funder_id')
    
    if funder_id:
        # Find specific profile for this funder
        profile = FunderProfile.query.filter_by(funder_id=funder_id, is_active=True).first()
        return jsonify({
            'profiles': [profile.to_dict(include_rules=True)] if profile else []
        }), 200
    
    # Return all active profiles for selection
    profiles = FunderProfile.query.filter_by(is_active=True).all()
    return jsonify({
        'profiles': [p.to_dict(include_rules=True) for p in profiles]
    }), 200

@rules_bp.route('/evaluate/check-draft', methods=['POST'])
@token_required
def check_draft(user):
    data = request.json
    funder_id = data.get('funder_id')
    partial_data = data.get('data')
    
    if not funder_id or not partial_data:
        return jsonify({'error': 'funder_id and data required'}), 400
        
    triggered_rules = RuleService.evaluate_draft(partial_data, funder_id)
    
    return jsonify({
        'triggered_rules': triggered_rules
    }), 200

# --- RSU ADMIN ENDPOINTS ---

@rules_bp.route('/rules', methods=['GET'])
@token_required
@rsu_required
def get_all_rules(user):
    rules = Rule.query.all()
    return jsonify([r.to_dict() for r in rules]), 200

@rules_bp.route('/rules', methods=['POST'])
@token_required
@rsu_required
def create_rule(user):
    data = request.json
    try:
        new_rule = Rule(
            name=data['name'],
            rule_type=data['rule_type'],
            logic_config=json.dumps(data['logic_config']),
            outcome=data['outcome'],
            priority_level=data.get('priority_level', 3),
            guidance_text=data.get('guidance_text'),
            created_by_id=user.id,
            is_active=True
        )
        db.session.add(new_rule)
        db.session.commit()
        return jsonify(new_rule.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@rules_bp.route('/evaluate/dry-run', methods=['POST'])
@token_required
@rsu_required
def dry_run(user):
    data = request.json
    context = data.get('context')
    rule_ids = data.get('rule_ids', [])
    
    if not context or not rule_ids:
        return jsonify({'error': 'context and rule_ids required'}), 400
        
    rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
    results = []
    for rule in rules:
        triggered, check_context = RuleService._check_rule(rule, context)
        results.append({
            'rule_id': rule.id,
            'name': rule.name,
            'triggered': triggered,
            'outcome': rule.outcome,
            'check_context': check_context
        })
        
    return jsonify({
        'simulation_results': results
    }), 200

@rules_bp.route('/evaluate/simulate', methods=['POST'])
@token_required
def simulate_action_outcome(user):
    """
    PI/Team level simulation of an action (virement, expense) before submission.
    No permanent evaluation records are created (commit=False).
    """
    data = request.json
    action_type = data.get('action_type') # e.g., BUDGET_REALLOCATION
    context = data.get('context')
    grant_id = data.get('grant_id')
    
    if not action_type or not context or not grant_id:
        return jsonify({'error': 'action_type, context, and grant_id required'}), 400
        
    # Construct evaluation context
    # Note: evaluate_action in RuleService handles rule lookups.
    # We pass it to evaluate_action but need to ENSURE it doesn't commit.
    # Actually, evaluate_action CURRENTLY commits. 
    # I should update evaluate_action to accept a commit flag.
    
    # For now, I'll bypass and call the logic manually or use the existing one if I updated it.
    # Wait, did I update evaluate_action to accept commit? Let me check.

@rules_bp.route('/rules/<int:rule_id>', methods=['PATCH'])
@token_required
@rsu_required
def update_rule(user, rule_id):
    rule = Rule.query.get_or_404(rule_id)
    data = request.json
    
    if 'is_active' in data:
        rule.is_active = data['is_active']
    if 'name' in data:
        rule.name = data['name']
    if 'outcome' in data:
        rule.outcome = data['outcome']
        
    db.session.commit()
    return jsonify(rule.to_dict()), 200

@rules_bp.route('/rules/stats', methods=['GET'])
@token_required
@rsu_required
def get_rule_stats(user):
    active_rules = Rule.query.filter_by(is_active=True).count()
    
    # Simple count of evaluations with outcome BLOCK in the last 30 days
    from sqlalchemy import func
    blocks = RuleEvaluation.query.filter(
        RuleEvaluation.final_outcome == 'BLOCK',
        RuleEvaluation.evaluated_at >= func.date('now', '-30 days')
    ).count()
    
    overrides = RuleEvaluation.query.filter(
        RuleEvaluation.final_outcome.in_(['PRIOR_APPROVAL', 'PENDING_COSIGN']),
        RuleEvaluation.resolution_outcome == None
    ).count()
    
    return jsonify({
        'activeRules': active_rules,
        'blocksThisMonth': blocks,
        'overridesPending': overrides
    }), 200

@rules_bp.route('/prior-approvals', methods=['GET'])
@token_required
@rsu_required
def get_prior_approval_requests(user):
    requests = PriorApprovalRequest.query.filter_by(status='pending').all()
    results = []
    for req in requests:
        res = req.to_dict()
        # Add some context for the UI
        grant = Grant.query.get(req.grant_id)
        requester = User.query.get(req.requester_id)
        res['grant_title'] = grant.title if grant else "Unknown"
        res['requester_name'] = requester.name if requester else "Unknown"
        results.append(res)
        
    return jsonify({
        'requests': results
    }), 200

@rules_bp.route('/prior-approvals/<int:request_id>/resolve', methods=['POST'])
@token_required
@rsu_required
def resolve_prior_approval_request(user, request_id):
    pa_request = PriorApprovalRequest.query.get_or_404(request_id)
    data = request.json
    decision = data.get('decision') # APPROVED | REJECTED
    justification = data.get('justification')
    
    if not decision or not justification:
        return jsonify({'error': 'decision and justification required'}), 400
        
    pa_request.status = decision.lower() # approved, rejected
    pa_request.resolved_by_id = user.id
    pa_request.resolved_at = datetime.utcnow()
    
    # Update the target object based on decision
    if pa_request.request_type == 'EXPENSE':
        expense = ExpenseClaim.query.get(pa_request.target_id)
        if expense:
            if decision == 'APPROVED':
                expense.status = 'pending' # Move to normal approval queue
            else:
                expense.status = 'rejected'
    
    elif pa_request.request_type == 'PERSONNEL':
        member = GrantTeam.query.get(pa_request.target_id)
        if member:
            if decision == 'APPROVED':
                member.status = 'active'
            else:
                db.session.delete(member) # Rejecting addition deletes the entry

    db.session.commit()
    
    # Notify PI
    from services.notification_service import NotificationService
    grant = Grant.query.get(pa_request.grant_id)
    if grant:
        NotificationService.notify_rule_event(
            grant.pi_id, 
            'PRIOR_APPROVAL_DECISION', 
            {
                'grant_id': grant.id,
                'request_type': pa_request.request_type,
                'status': decision,
                'approved': decision == 'APPROVED',
                'notes': justification
            }
        )
    
    return jsonify({'message': f'Request {decision.lower()} successfully.'}), 200

@rules_bp.route('/rule-exemptions', methods=['POST'])
@token_required
@rsu_required
def create_rule_exemption(user):
    data = request.json
    try:
        exemption = RuleExemption(
            grant_id=data['grant_id'],
            rule_id=data['rule_id'],
            justification=data['justification'],
            approved_by_id=user.id
        )
        db.session.add(exemption)
        db.session.commit()
        return jsonify(exemption.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@rules_bp.route('/rule-exemptions/grant/<int:grant_id>', methods=['GET'])
@token_required
def get_grant_exemptions(user, grant_id):
    exemptions = RuleExemption.query.filter_by(grant_id=grant_id, is_active=True).all()
    return jsonify([e.to_dict() for e in exemptions]), 200

@rules_bp.route('/profiles', methods=['GET'])
@token_required
@rsu_required
def get_profiles(user):
    profiles = FunderProfile.query.all()
    return jsonify([p.to_dict(include_rules=True) for p in profiles]), 200

@rules_bp.route('/profiles', methods=['POST'])
@token_required
@rsu_required
def create_profile(user):
    data = request.json
    try:
        profile = FunderProfile(
            name=data['name'],
            funder_id=data.get('funder_id'),
            created_by_id=user.id
        )
        db.session.add(profile)
        
        # Link rules
        if 'rule_ids' in data:
            rules = Rule.query.filter(Rule.id.in_(data['rule_ids'])).all()
            profile.rules = rules
            
        db.session.commit()
        return jsonify(profile.to_dict(include_rules=True)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@rules_bp.route('/evaluation/<int:evaluation_id>/resolve', methods=['POST'])
@token_required
@rsu_required
def resolve_evaluation(user, evaluation_id):
    eval_record = RuleEvaluation.query.get_or_404(evaluation_id)
    data = request.json
    decision = data.get('decision') # APPROVED | REJECTED
    justification = data.get('justification')
    
    if not decision or not justification:
        return jsonify({'error': 'decision and justification required'}), 400
        
    # Check for context threshold (e.g. > MWK 5,000,000 requires dual signoff)
    context = json.loads(eval_record.context_snapshot or '{}')
    amount = float(context.get('amount', 0))
    
    HIGH_VALUE_THRESHOLD = 5000000 # 5M MWK
    
    if amount > HIGH_VALUE_THRESHOLD:
        if not eval_record.override_cosigned_by:
            if eval_record.resolution_outcome != 'PENDING_COSIGN':
                eval_record.resolved_by_id = user.id
                eval_record.override_justification = justification
                eval_record.resolution_outcome = 'PENDING_COSIGN'
                db.session.commit()
                return jsonify({'message': 'High-value override recorded. Awaiting second RSU sign-off.'}), 200
        elif eval_record.resolved_by_id == user.id:
            return jsonify({'error': 'The same staff member cannot co-sign their own override.'}), 400
    
    if eval_record.resolution_outcome == 'PENDING_COSIGN':
        eval_record.override_cosigned_by = user.id
    else:
        eval_record.resolved_by_id = user.id
        
    eval_record.resolved_at = datetime.utcnow()
    eval_record.resolution_outcome = decision
    eval_record.override_justification = justification
    
    from models import ExpenseClaim
    expense = ExpenseClaim.query.filter_by(rule_evaluation_id=evaluation_id).first()
    if expense:
        if decision == 'APPROVED':
            expense.status = 'pending'
        else:
            expense.status = 'rejected'
            
    db.session.commit()
    
    from services.notification_service import NotificationService
    grant = eval_record.grant
    NotificationService.notify_rule_event(
        grant.pi_id, 
        'PRIOR_APPROVAL_DECISION', 
        {
            'grant_id': grant.id,
            'status': decision,
            'approved': decision == 'APPROVED',
            'notes': justification
        }
    )
    
    return jsonify({'message': f'Resolution recorded as {decision}'}), 200

# --- ENHANCED RULE ENGINE ENDPOINTS ---

@rules_bp.route('/enhanced/evaluate', methods=['POST'])
@token_required
def enhanced_evaluate(user):
    """
    Enhanced rule evaluation with context awareness and predictive risk assessment
    """
    data = request.json
    action_type = data.get('action_type')
    context = data.get('context')
    grant_id = data.get('grant_id')
    
    if not action_type or not context or not grant_id:
        return jsonify({'error': 'action_type, context, and grant_id required'}), 400
    
    # Add user context
    user_context = {
        'user_id': user.id,
        'user_role': user.role
    }
    
    result = EnhancedRuleService.evaluate_with_context(
        action_type, context, grant_id, user_context
    )
    
    return jsonify(result), 200

@rules_bp.route('/enhanced/compliance-dashboard', methods=['GET'])
@token_required
@rsu_required
def get_compliance_dashboard(user):
    """Get comprehensive compliance dashboard"""
    dashboard = RuleEnforcementService.get_compliance_dashboard()
    return jsonify(dashboard), 200

@rules_bp.route('/enhanced/system-compliance', methods=['GET'])
@token_required
@rsu_required
def check_system_compliance(user):
    """Check overall system compliance"""
    compliance = RuleEnforcementService.monitor_system_compliance()
    return jsonify(compliance), 200

@rules_bp.route('/enhanced/enforce-violations', methods=['POST'])
@token_required
@rsu_required
def enforce_violations(user):
    """Manually trigger enforcement of rule violations"""
    data = request.json
    violations = data.get('violations', [])
    
    if not violations:
        # Get current violations if none provided
        compliance = RuleEnforcementService.monitor_system_compliance()
        violations = compliance['issues']
    
    actions = RuleEnforcementService.enforce_rule_violations(violations)
    
    return jsonify({
        'violations_processed': len(violations),
        'enforcement_actions': actions,
        'processed_at': datetime.utcnow().isoformat()
    }), 200

@rules_bp.route('/enhanced/compliance-trends/<int:grant_id>', methods=['GET'])
@token_required
def get_compliance_trends(user, grant_id):
    """Get compliance trends for a specific grant"""
    days = request.args.get('days', 30, type=int)
    trends = EnhancedRuleService.get_compliance_trends(grant_id, days)
    return jsonify(trends), 200

@rules_bp.route('/enhanced/predictive-risk', methods=['POST'])
@token_required
def assess_predictive_risk(user):
    """Assess predictive risk for a proposed action"""
    data = request.json
    action_type = data.get('action_type')
    context = data.get('context')
    grant_id = data.get('grant_id')
    
    if not action_type or not context or not grant_id:
        return jsonify({'error': 'action_type, context, and grant_id required'}), 400
    
    risk_assessment = EnhancedRuleService._assess_predictive_risk(
        action_type, context, grant_id
    )
    
    return jsonify(risk_assessment), 200

@rules_bp.route('/enhanced/grant-risk/<int:grant_id>', methods=['GET'])
@token_required
def get_grant_risk_assessment(user, grant_id):
    """Get comprehensive risk assessment for a grant"""
    grant = Grant.query.get_or_404(grant_id)
    
    # Get compliance score
    compliance_score = EnhancedRuleService._calculate_compliance_score(grant_id)
    
    # Get budget utilization
    budget_util = EnhancedRuleService._get_budget_utilization(grant_id)
    
    # Get time context
    time_context = EnhancedRuleService._get_time_context(grant)
    
    # Assess overall risk
    risk_level = EnhancedRuleService._assess_grant_risk_level(grant)
    
    return jsonify({
        'grant_id': grant_id,
        'risk_level': risk_level,
        'compliance_score': compliance_score,
        'budget_utilization': budget_util,
        'time_context': time_context,
        'assessed_at': datetime.utcnow().isoformat()
    }), 200

# --- BURN RATE & FORECASTING ENDPOINTS ---

@rules_bp.route('/burn-rate/<int:grant_id>', methods=['GET'])
@token_required
def get_burn_rate(user, grant_id):
    """Get burn rate analysis for a grant"""
    from services.burn_rate_service import BurnRateService
    
    force_recalculate = request.args.get('force', 'false').lower() == 'true'
    
    try:
        burn_rate = BurnRateService.calculate_burn_rate(grant_id, force_recalculate)
        
        return jsonify({
            'burn_rate': burn_rate,
            'grant_id': grant_id,
            'calculated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to calculate burn rate: {str(e)}'}), 500

@rules_bp.route('/burn-rate/<int:grant_id>/trends', methods=['GET'])
@token_required
def get_burn_rate_trends(user, grant_id):
    """Get burn rate trends over time"""
    from services.burn_rate_service import BurnRateService
    
    days = request.args.get('days', 90, type=int)
    
    if days < 7 or days > 365:
        return jsonify({'error': 'days must be between 7 and 365'}), 400
    
    try:
        trends = BurnRateService.get_burn_rate_trends(grant_id, days)
        
        return jsonify({
            'trends': trends,
            'grant_id': grant_id,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get burn rate trends: {str(e)}'}), 500

@rules_bp.route('/burn-rate/summary', methods=['GET'])
@token_required
@rsu_required
def get_burn_rate_summary(user):
    """Get system-wide burn rate summary"""
    from services.burn_rate_service import BurnRateService
    
    try:
        summary = BurnRateService.get_system_burn_rate_summary()
        
        return jsonify({
            'summary': summary,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get burn rate summary: {str(e)}'}), 500

@rules_bp.route('/burn-rate/alerts', methods=['GET'])
@token_required
@rsu_required
def get_burn_rate_alerts(user):
    """Get burn rate alerts for grants needing attention"""
    from services.burn_rate_service import BurnRateService
    
    try:
        alerts = BurnRateService.get_burn_rate_alerts()
        
        return jsonify({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get burn rate alerts: {str(e)}'}), 500

@rules_bp.route('/burn-rate/<int:grant_id>/projected-completion', methods=['GET'])
@token_required
def get_projected_completion(user, grant_id):
    """Get projected completion based on current burn rate"""
    from services.burn_rate_service import BurnRateService
    
    try:
        projection = BurnRateService.calculate_projected_completion(grant_id)
        
        return jsonify({
            'projection': projection,
            'grant_id': grant_id,
            'calculated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to calculate projected completion: {str(e)}'}), 500

@rules_bp.route('/forecast/<int:grant_id>', methods=['GET'])
@token_required
def get_budget_forecast(user, grant_id):
    """Get budget forecast for a grant"""
    from services.budget_forecasting_service import BudgetForecastingService
    
    force_recalculate = request.args.get('force', 'false').lower() == 'true'
    
    try:
        forecast = BudgetForecastingService.calculate_forecast(grant_id, force_recalculate)
        
        return jsonify({
            'forecast': forecast,
            'grant_id': grant_id,
            'calculated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to calculate budget forecast: {str(e)}'}), 500

@rules_bp.route('/forecast/<int:grant_id>/what-if', methods=['POST'])
@token_required
def what_if_forecast(user, grant_id):
    """Calculate what-if scenarios for budget planning"""
    from services.budget_forecasting_service import BudgetForecastingService
    
    scenario_changes = request.json
    
    if not scenario_changes:
        return jsonify({'error': 'scenario_changes are required in request body'}), 400
    
    # Validate scenario structure
    allowed_keys = ['new_personnel', 'equipment_purchase', 'travel_increase', 'other_costs']
    for key in scenario_changes:
        if key not in allowed_keys:
            return jsonify({'error': f'Invalid scenario key: {key}'}), 400
    
    try:
        result = BudgetForecastingService.what_if_scenario(grant_id, scenario_changes)
        
        return jsonify({
            'scenario_result': result,
            'grant_id': grant_id,
            'scenario_changes': scenario_changes,
            'calculated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to calculate what-if scenario: {str(e)}'}), 500

@rules_bp.route('/forecast/summary', methods=['GET'])
@token_required
@rsu_required
def get_forecast_summary(user):
    """Get system-wide forecast summary"""
    from services.budget_forecasting_service import BudgetForecastingService
    
    try:
        summary = BudgetForecastingService.get_forecast_summary()
        
        return jsonify({
            'summary': summary,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get forecast summary: {str(e)}'}), 500

@rules_bp.route('/forecast/<int:grant_id>/health', methods=['GET'])
@token_required
def get_financial_health(user, grant_id):
    """Get comprehensive financial health indicators for a grant"""
    from services.budget_forecasting_service import BudgetForecastingService
    
    try:
        health = BudgetForecastingService.get_financial_health_indicators(grant_id)
        
        return jsonify({
            'financial_health': health,
            'grant_id': grant_id,
            'assessed_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get financial health indicators: {str(e)}'}), 500

@rules_bp.route('/financial-dashboard', methods=['GET'])
@token_required
def get_financial_dashboard(user):
    """Get comprehensive financial dashboard data"""
    from services.burn_rate_service import BurnRateService
    from services.budget_forecasting_service import BudgetForecastingService
    
    grant_id = request.args.get('grant_id', type=int)
    
    if not grant_id:
        return jsonify({'error': 'grant_id is required'}), 400
    
    try:
        # Get all financial data for the grant
        burn_rate = BurnRateService.calculate_burn_rate(grant_id)
        forecast = BudgetForecastingService.calculate_forecast(grant_id)
        health = BudgetForecastingService.get_financial_health_indicators(grant_id)
        trends = BurnRateService.get_burn_rate_trends(grant_id, 90)
        
        return jsonify({
            'grant_id': grant_id,
            'burn_rate': burn_rate,
            'forecast': forecast,
            'financial_health': health,
            'trends': trends,
            'dashboard_generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate financial dashboard: {str(e)}'}), 500

@rules_bp.route('/system-financial-overview', methods=['GET'])
@token_required
@rsu_required
def get_system_financial_overview(user):
    """Get system-wide financial overview for RSU dashboard"""
    from services.burn_rate_service import BurnRateService
    from services.budget_forecasting_service import BudgetForecastingService
    
    try:
        # Get system-wide summaries
        burn_rate_summary = BurnRateService.get_system_burn_rate_summary()
        forecast_summary = BudgetForecastingService.get_forecast_summary()
        burn_rate_alerts = BurnRateService.get_burn_rate_alerts()
        
        # Combine critical grants from both summaries
        critical_grants = []
        
        # Add burn rate critical grants
        for grant in burn_rate_summary.get('critical_grants', []):
            grant['critical_type'] = 'BURN_RATE'
            critical_grants.append(grant)
        
        # Add forecast high-risk grants
        for grant in forecast_summary.get('high_risk_grants', []):
            grant['critical_type'] = 'FORECAST_RISK'
            critical_grants.append(grant)
        
        # Remove duplicates and sort by severity
        unique_grants = {}
        for grant in critical_grants:
            grant_id = grant['grant_id']
            if grant_id not in unique_grants:
                unique_grants[grant_id] = grant
            else:
                # Merge critical types if grant appears in both
                existing = unique_grants[grant_id]
                if 'critical_types' not in existing:
                    existing['critical_types'] = [existing['critical_type']]
                if grant['critical_type'] not in existing['critical_types']:
                    existing['critical_types'].append(grant['critical_type'])
        
        critical_grants = list(unique_grants.values())
        
        return jsonify({
            'burn_rate_summary': burn_rate_summary,
            'forecast_summary': forecast_summary,
            'alerts': burn_rate_alerts,
            'critical_grants': critical_grants,
            'total_critical_grants': len(critical_grants),
            'overview_generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get system financial overview: {str(e)}'}), 500
