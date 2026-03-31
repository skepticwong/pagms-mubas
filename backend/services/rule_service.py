import json
from datetime import datetime
from models import db, Grant, RuleSnapshot, RuleEvaluation, AuditTrail

class RuleService:
    @staticmethod
    def evaluate_action(domain, payload, grant_id, user_id=None, ip_address=None):
        """
        The Core Logic Processor. 
        Implements 'Strictest Penalty Wins' algorithm.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            return {'outcome': 'PASS', 'triggered_rules': []}

        # 1. Ethics Compliance Gating (Hard Gate)
        if grant.ethics_required and grant.ethics_status in ['PENDING_ETHICS', 'SUSPENDED_ETHICS']:
            status_display = "pending RSU verification" if grant.ethics_status == 'PENDING_ETHICS' else "suspended due to expiry"
            return {
                'outcome': 'BLOCK',
                'triggered_rules': [{
                    'name': 'ETHICS_GATING_LOCK',
                    'outcome': 'BLOCK',
                    'guidance': f'This grant is currently {status_display}. All compliance-tracked actions are locked.'
                }]
            }

        # 2. Load context (Immutable Snapshot)
        snapshot = RuleSnapshot.query.filter_by(grant_id=grant_id).first()
        if not snapshot:
            # Fail Secure: If rules are missing for active grants, BLOCK.
            if grant.status == 'ACTIVE':
                return {
                    'outcome': 'BLOCK',
                    'triggered_rules': [{'name': 'MISSING_RULES', 'outcome': 'BLOCK', 'guidance': 'Compliance rules not found.'}]
                }
            return {'outcome': 'PASS', 'triggered_rules': []}

        rules = snapshot.rules_json
        
        # 2. Filter Rules by Domain (e.g., "EXPENSE", "PERSONNEL")
        domain_rules = [r for r in rules if r.get('domain') == domain.upper()]
        
        if not domain_rules:
            return {'outcome': 'PASS', 'triggered_rules': []}

        # 3. Evaluate Rules against Payload
        triggered_results = []
        for rule in domain_rules:
            triggered, context = RuleService._check_logic(rule, payload)
            if triggered:
                triggered_results.append({
                    'name': rule.get('name'),
                    'outcome': rule.get('outcome'),
                    'guidance': rule.get('guidance_text')
                })

        if not triggered_results:
            return {'outcome': 'PASS', 'triggered_rules': []}

        # 4. Resolve Outcome (Strictest Penalty Wins)
        # BLOCK > PRIOR_APPROVAL > WARN > PASS
        priority_map = {'BLOCK': 0, 'PRIOR_APPROVAL': 1, 'WARN': 2, 'PASS': 3}
        triggered_results.sort(key=lambda x: priority_map.get(x['outcome'], 99))
        final_outcome = triggered_results[0]['outcome']

        # 5. Enrich & Log (Audit-Proof Security)
        eval_record = RuleEvaluation(
            grant_id=grant_id,
            user_id=user_id,
            action_type=domain,
            target_id=payload.get('id'), # ID of the target entity if available
            outcome=final_outcome,
            triggered_rules=triggered_results,
            timestamp=datetime.utcnow(),
            ip_address=ip_address
        )
        db.session.add(eval_record)
        
        # Log to global Audit Trail if outcome is significant
        if final_outcome in ['BLOCK', 'PRIOR_APPROVAL']:
            audit = AuditTrail(
                user_id=user_id,
                action=f'RULE_{final_outcome}',
                entity_type=domain,
                entity_id=payload.get('id'),
                details={'triggered_rules': [r['name'] for r in triggered_results]},
                timestamp=datetime.utcnow(),
                ip_address=ip_address
            )
            db.session.add(audit)

        db.session.commit()

        return {
            'outcome': final_outcome,
            'triggered_rules': triggered_results,
            'evaluation_id': eval_record.id
        }

    @staticmethod
    def _check_logic(rule, context):
        """
        Standardized rule logic checker.
        Supports: '>', '<', '==', '!=', 'contains', 'is_missing'.
        Now handles both new 'condition/value' and legacy 'op/val' keys.
        """
        config = rule.get('logic_config') or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except:
                config = {}

        field = config.get('category') or config.get('field') or rule.get('field')
        op = config.get('condition') or config.get('op') or config.get('operator') or rule.get('op')
        val = config.get('value') or config.get('val') or rule.get('value')

        if not field or not op:
            return False, "Missing logic definition"

        actual_value = context.get(field)
        if actual_value is None:
            return False, None

        try:
            # Type casting for numeric comparisons
            if isinstance(val, (int, float)):
                actual_value = float(actual_value)
        except:
            pass

        triggered = False
        if op == '>':
            triggered = actual_value > val
        elif op == '<':
            triggered = actual_value < val
        elif op == '==':
            triggered = str(actual_value) == str(val)
        elif op == '!=':
            triggered = str(actual_value) != str(val)
        elif op == 'in_list':
            triggered = actual_value in val
        elif op == 'not_in_list':
            triggered = actual_value not in val

        return triggered, {'actual': actual_value, 'threshold': val}
