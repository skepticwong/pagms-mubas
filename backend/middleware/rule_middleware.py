"""
Rule Middleware - Automatic rule enforcement across all API endpoints
Provides real-time rule checking and enforcement for maximum system control.
"""

import json
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime
from services.enhanced_rule_service import EnhancedRuleService
from services.rule_enforcement_service import RuleEnforcementService

class RuleMiddleware:
    """Middleware for automatic rule enforcement across the system"""
    
    @staticmethod
    def enforce_rules(action_type: str, get_grant_id_func=None, get_context_func=None):
        """
        Decorator for automatic rule enforcement on API endpoints
        
        Usage:
        @RuleMiddleware.enforce_rules('EXPENSE_SUBMISSION', 
                                     get_grant_id_func=lambda: request.json.get('grant_id'),
                                     get_context_func=lambda: request.json)
        def create_expense():
            # Your endpoint logic here
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get grant ID and context
                grant_id = get_grant_id_func() if get_grant_id_func else None
                context = get_context_func() if get_context_func else {}
                
                if not grant_id:
                    return jsonify({'error': 'Grant ID required for rule evaluation'}), 400
                
                # Add user context if available
                if hasattr(g, 'user'):
                    context['user_id'] = g.user.id
                    context['user_role'] = g.user.role
                
                # Perform enhanced rule evaluation
                evaluation_result = EnhancedRuleService.evaluate_with_context(
                    action_type, context, grant_id, {'user_id': context.get('user_id')}
                )
                
                # Check if action is blocked
                if evaluation_result['outcome'] == 'BLOCK':
                    return jsonify({
                        'error': 'Action blocked by compliance rules',
                        'evaluation': evaluation_result,
                        'blocked': True
                    }), 403
                
                # Add warnings to response context
                if evaluation_result['outcome'] in ['WARN', 'PRIOR_APPROVAL']:
                    # Store evaluation result for later use
                    g.rule_evaluation = evaluation_result
                
                # Continue with the original function
                result = f(*args, **kwargs)
                
                # If this is a successful creation/update, log the evaluation
                if hasattr(g, 'rule_evaluation') and isinstance(result, tuple):
                    status_code = result[1] if len(result) > 1 else 200
                    if 200 <= status_code < 300:
                        # Log successful evaluation
                        RuleMiddleware._log_evaluation(
                            grant_id, action_type, context, g.rule_evaluation
                        )
                
                return result
            return decorated_function
        return decorator
    
    @staticmethod
    def _log_evaluation(grant_id: int, action_type: str, context: dict, evaluation: dict):
        """Log rule evaluation for audit trail"""
        # This would integrate with your existing RuleEvaluation model
        # For now, we'll just log it (in production, you'd save to database)
        print(f"RULE_EVALUATION_LOG: {datetime.utcnow()} - Grant {grant_id} - {action_type} - {evaluation['outcome']}")
    
    @staticmethod
    def check_system_compliance():
        """Check overall system compliance - can be called periodically"""
        compliance_result = RuleEnforcementService.monitor_system_compliance()
        
        # Auto-enforce critical violations
        if compliance_result['total_issues'] > 0:
            critical_issues = [i for i in compliance_result['issues'] if i.get('severity') == 'CRITICAL']
            if critical_issues:
                RuleEnforcementService.enforce_rule_violations(critical_issues)
        
        return compliance_result

# Predefined middleware decorators for common actions
enforce_expense_rules = RuleMiddleware.enforce_rules(
    'EXPENSE_SUBMISSION',
    get_grant_id_func=lambda: request.json.get('grant_id'),
    get_context_func=lambda: request.json
)

enforce_personnel_rules = RuleMiddleware.enforce_rules(
    'PERSONNEL_CHANGE',
    get_grant_id_func=lambda: request.json.get('grant_id'),
    get_context_func=lambda: request.json
)

enforce_virement_rules = RuleMiddleware.enforce_rules(
    'BUDGET_REALLOCATION',
    get_grant_id_func=lambda: request.json.get('grant_id'),
    get_context_func=lambda: request.json
)

enforce_modification_rules = RuleMiddleware.enforce_rules(
    'GRANT_MODIFICATION',
    get_grant_id_func=lambda: request.json.get('grant_id'),
    get_context_func=lambda: request.json
)
