from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from models import db, Rule, RuleProfile, RuleEvaluation, User, PriorApprovalRequest, RuleExemption, ExpenseClaim, GrantTeam, Grant
from services.rule_service import RuleService
from middleware import token_required, rsu_required

rules_bp = Blueprint('rules', __name__)

@rules_bp.route('/rule-profiles/active', methods=['GET'])
@token_required
def get_active_profiles(user):
    funder_id = request.args.get('funder_id')
    
    if funder_id:
        # Find specific profile for this funder
        profile = RuleProfile.query.filter_by(funder_id=funder_id, is_active=True).first()
        return jsonify({
            'profiles': [profile.to_dict(include_rules=True)] if profile else []
        }), 200
    
    # Return all active profiles for selection
    profiles = RuleProfile.query.filter_by(is_active=True).all()
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
    profiles = RuleProfile.query.all()
    return jsonify([p.to_dict(include_rules=True) for p in profiles]), 200

@rules_bp.route('/profiles', methods=['POST'])
@token_required
@rsu_required
def create_profile(user):
    data = request.json
    try:
        profile = RuleProfile(
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
