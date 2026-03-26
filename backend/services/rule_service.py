import json
from datetime import datetime
from models import db, Grant, Rule, RuleProfile, RuleProfileSnapshot, RuleEvaluation, RuleExemption

class RuleService:
    @staticmethod
    def evaluate_draft(partial_data, funder_id):
        """
        Lightweight check for the draft phase. 
        Returns warnings/guidance based on the active profile for a funder.
        """
        active_profile = RuleProfile.query.filter_by(funder_id=funder_id, is_active=True).first()
        if not active_profile:
            return []

        triggered_rules = []
        for rule in active_profile.rules:
            if not rule.is_active:
                continue
            
            triggered, context = RuleService._check_rule(rule, partial_data)
            if triggered:
                triggered_rules.append({
                    'rule_id': rule.id,
                    'name': rule.name,
                    'outcome': rule.outcome,
                    'guidance_text': rule.guidance_text,
                    'priority': rule.priority_level
                })
        
        return triggered_rules

    @staticmethod
    def validate_grant_creation(data, funder_id):
        """
        Higher-level validation for grant creation.
        Returns a structured result with blocks and warnings.
        Looks up the profile by rule_profile_id in data first, then by funder_id.
        """
        # Try direct profile lookup by ID first (most accurate)
        profile_id = data.get('rule_profile_id')
        if profile_id:
            profile = RuleProfile.query.get(int(profile_id))
            if profile and profile.is_active:
                triggered_rules = []
                for rule in profile.rules:
                    if not rule.is_active:
                        continue
                    triggered, context = RuleService._check_rule(rule, data)
                    if triggered:
                        triggered_rules.append({
                            'rule_id': rule.id,
                            'name': rule.name,
                            'outcome': rule.outcome,
                            'guidance_text': rule.guidance_text,
                            'priority': rule.priority_level
                        })
                triggered = triggered_rules
            else:
                triggered = []
        else:
            triggered = RuleService.evaluate_draft(data, funder_id)
        
        has_blocks = any(r['outcome'] == 'BLOCK' for r in triggered)
        has_warnings = any(r['outcome'] == 'WARN' for r in triggered)
        has_prior_approvals = any(r['outcome'] == 'PRIOR_APPROVAL' for r in triggered)
        
        return {
            'has_blocks': has_blocks,
            'has_warnings': has_warnings,
            'has_prior_approvals': has_prior_approvals,
            'block_reasons': [r['guidance_text'] for r in triggered if r['outcome'] == 'BLOCK'],
            'warnings': [r['guidance_text'] for r in triggered if r['outcome'] == 'WARN'],
            'prior_approval_reasons': [r['guidance_text'] for r in triggered if r['outcome'] == 'PRIOR_APPROVAL'],
            'triggered_rules': triggered
        }

    @staticmethod
    def evaluate_expense(expense_data, grant_id):
        """Processes an expense through the grant's rule profile."""
        return RuleService.evaluate_action('EXPENSE_SUBMISSION', expense_data, grant_id)

    @staticmethod
    def check_personnel_change(grant_id, member_data, change_type="addition"):
        """Evaluates rules for adding/removing team members."""
        context = {
            'category': 'personnel',
            'role': member_data.get('role'),
            'change_type': change_type,
            'user_id': member_data.get('user_id'),
            'pay_rate': member_data.get('pay_rate')
        }
        return RuleService.evaluate_action('PERSONNEL_CHANGE', context, grant_id)

    @staticmethod
    def evaluate_modification(grant_id, modification_data):
        """Evaluates rules for budget reallocations or NCEs."""
        # Ensure category is set for rule matching
        if 'category' not in modification_data:
            modification_data['category'] = 'modification'
        return RuleService.evaluate_action('BUDGET_REALLOCATION', modification_data, grant_id)

    @staticmethod
    def evaluate_action(action_type, context, grant_id):
        """Generic evaluator for any action (Personnel, Travel, etc.)"""
        grant = Grant.query.get(grant_id)
        if not grant:
            return {'outcome': 'PASS', 'triggered_rules': []}

        # Determine which rules to use: Snapshot first, then Profile
        rules = []
        if grant.rule_snapshot_id:
            snapshot = RuleProfileSnapshot.query.get(grant.rule_snapshot_id)
            if snapshot:
                rules_data = json.loads(snapshot.snapshot_data)
                # Reconstruct Rule-like objects from snapshot data
                rules = rules_data
        elif grant.rule_profile_id:
            profile = RuleProfile.query.get(grant.rule_profile_id)
            if profile:
                rules = [r.to_dict() for r in profile.rules if r.is_active]

        if not rules:
            return {'outcome': 'PASS', 'triggered_rules': []}

        triggered_results = []
        for rule_data in rules:
            rule_id = rule_data.get('id')
            
            # Check for grant-specific exemption (Whitelisting)
            if rule_id:
                exemption = RuleExemption.query.filter_by(
                    grant_id=grant_id, 
                    rule_id=rule_id, 
                    is_active=True
                ).first()
                if exemption:
                    continue # Rule is whitelisted for this grant

            triggered, check_context = RuleService._check_rule_logic(rule_data['logic_config'], context)
            if triggered:
                triggered_results.append({
                    'rule_id': rule_id,
                    'name': rule_data['name'],
                    'outcome': rule_data['outcome'],
                    'guidance_text': rule_data.get('guidance_text'),
                    'priority': rule_data.get('priority_level', 3)
                })

        if not triggered_results:
            return {'outcome': 'PASS', 'triggered_rules': [], 'evaluation_ids': []}

        # Resolve final outcome priority: BLOCK > PRIOR_APPROVAL > WARN
        outcome_map = {'BLOCK': 0, 'PRIOR_APPROVAL': 1, 'WARN': 2}
        
        # Sort by outcomes (most restrictive first) and then priority level
        triggered_results.sort(key=lambda x: (outcome_map.get(x['outcome'], 99), x['priority']))
        final_outcome = triggered_results[0]['outcome']

        # Log Individual Evaluations for each triggered rule (Audit Trail)
        evaluation_ids = []
        for res in triggered_results:
            eval_record = RuleEvaluation(
                grant_id=grant_id,
                rule_id=res['rule_id'],
                action_type=action_type,
                context_snapshot=json.dumps(context),
                triggered_outcome=res['outcome'],
                final_outcome=res['outcome'], # Initially same, might be overridden later
                evaluated_at=datetime.utcnow()
            )
            db.session.add(eval_record)
            db.session.flush() # Get ID before commit
            evaluation_ids.append(eval_record.id)
        
        db.session.commit()

        return {
            'evaluation_ids': evaluation_ids,
            'outcome': final_outcome,
            'triggered_rules': triggered_results
        }

    @staticmethod
    def _check_rule(rule, context):
        """Helper for Rule objects"""
        logic = json.loads(rule.logic_config)
        return RuleService._check_rule_logic(logic, context)

    @staticmethod
    def _check_rule_logic(logic, context):
        """
        The heart of the engine. Evaluates logic_config against context.
        Schema: { "field": "amount", "operator": "greater_than", "value": 5000, ... }
        """
        field = logic.get('field')
        operator = logic.get('operator')
        threshold = logic.get('value')
        applies_to = logic.get('applies_to') # e.g. "equipment"

        # 1. Filter by application scope if specified
        if applies_to and context.get('category', '').lower() != applies_to.lower():
            # If the rule only applies to 'equipment' but this is 'travel', it doesn't trigger
            return False, None

        actual_value = context.get(field)
        if actual_value is None and operator not in ['is_empty', 'is_not_empty']:
            return False, None

        # Cast to same type if possible
        try:
            if isinstance(threshold, (int, float)):
                actual_value = float(actual_value)
        except:
            pass

        triggered = False
        if operator == 'greater_than':
            triggered = actual_value > threshold
        elif operator == 'less_than':
            triggered = actual_value < threshold
        elif operator == 'equals':
            triggered = str(actual_value) == str(threshold)
        elif operator == 'not_in_list':
            triggered = actual_value not in threshold
        elif operator == 'below_minimum':
            triggered = actual_value < threshold
        elif operator == 'is_empty':
            triggered = not actual_value or str(actual_value).strip() == ""
        elif operator == 'is_not_empty':
            triggered = bool(actual_value and str(actual_value).strip() != "")
        elif operator == 'outside_date_range':
            # threshold would be [start, end]
            triggered = actual_value < threshold[0] or actual_value > threshold[1]

        return triggered, {'actual': actual_value, 'threshold': threshold}
