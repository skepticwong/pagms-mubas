"""
Tranche Validation Service
Phase 1: Business Rules Engine for Tranche Amendments
"""
import json
from datetime import datetime, date

# Import models with error handling
try:
    from models import db, Tranche, Milestone, Grant
except ImportError as e:
    print(f"TrancheValidationService: Error importing models: {e}")
    try:
        from models import db, Milestone, Grant
        from models import Tranche
    except ImportError as e2:
        print(f"TrancheValidationService: Still error importing models: {e2}")
        raise

class TrancheValidationService:
    """Service to enforce business rules for tranche operations"""
    
    @staticmethod
    def validate_tranche_amendment(grant_id, tranche_id, amendments):
        """
        Enforce business rules for tranche modifications
        
        Args:
            grant_id: ID of the grant
            tranche_id: ID of the tranche being amended
            amendments: Dict of proposed changes
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            tranche = Tranche.query.get(tranche_id)
            grant = Grant.query.get(grant_id)
            
            if not tranche or not grant:
                errors.append("Tranche or Grant not found")
                return errors
            
            # Rule 1: No retroactive unlocking
            if amendments.get('trigger_type') == 'milestone':
                new_milestone_id = amendments.get('triggering_milestone_id')
                if new_milestone_id:
                    milestone = Milestone.query.get(new_milestone_id)
                    comp = getattr(milestone, 'completion_date', None) if milestone else None
                    if milestone and comp:
                        comp_date = comp.date() if hasattr(comp, 'date') else comp
                        if tranche.expected_date < comp_date:
                            errors.append("Cannot set retroactive trigger: milestone completion date is after tranche expected date")
            
            # Rule 2: Total sum validation
            if amendments.get('amount') is not None:
                new_amount = float(amendments.get('amount'))
                
                # Get all other tranches for this grant (excluding this one)
                other_tranches = Tranche.query.filter(
                    Tranche.grant_id == grant_id,
                    Tranche.id != tranche_id,
                    Tranche.status != 'archived'
                ).all()
                
                total_other = sum(t.amount for t in other_tranches)
                total_with_new = total_other + new_amount
                
                if total_with_new > grant.total_budget:
                    errors.append(f"Total tranches (${total_with_new:,.2f}) exceed grant budget (${grant.total_budget:,.2f})")
                
                if new_amount <= 0:
                    errors.append("Tranche amount must be greater than 0")
            
            # Rule 3: Released tranches are locked
            if tranche.status == 'released':
                locked_fields = ['amount', 'trigger_type', 'triggering_milestone_id', 'expected_date']
                for field in locked_fields:
                    if field in amendments and amendments.get(field) != getattr(tranche, field):
                        errors.append(f"Cannot modify {field} for released tranches")
                        break
            
            # Rule 4: Trigger validation
            trigger_type = amendments.get('trigger_type', tranche.trigger_type)
            
            if trigger_type == 'milestone':
                milestone_id = amendments.get('triggering_milestone_id', tranche.triggering_milestone_id)
                if not milestone_id:
                    errors.append("Milestone trigger requires a valid milestone ID")
                else:
                    milestone = Milestone.query.get(milestone_id)
                    if not milestone:
                        errors.append("Specified milestone not found")
                    elif milestone.grant_id != grant_id:
                        errors.append("Milestone must belong to the same grant")
            
            elif trigger_type == 'report':
                report_type = amendments.get('required_report_type', tranche.required_report_type)
                if not report_type:
                    errors.append("Report trigger requires a valid report type")
                elif report_type not in ['financial', 'progress', 'technical']:
                    errors.append("Invalid report type. Must be: financial, progress, or technical")
            
            elif trigger_type == 'date':
                trigger_date = amendments.get('trigger_date', tranche.trigger_date)
                if not trigger_date:
                    errors.append("Date trigger requires a valid trigger date")
                else:
                    if isinstance(trigger_date, str):
                        trigger_date = datetime.strptime(trigger_date, '%Y-%m-%d').date()
                    if trigger_date < date.today():
                        errors.append("Trigger date cannot be in the past")
            
            # Rule 5: Date validation
            if amendments.get('expected_date'):
                try:
                    new_date = datetime.strptime(amendments.get('expected_date'), '%Y-%m-%d').date()
                    if new_date < date.today():
                        errors.append("Expected date cannot be in the past")
                    if new_date < grant.start_date:
                        errors.append("Expected date cannot be before grant start date")
                    if new_date > grant.end_date:
                        errors.append("Expected date cannot be after grant end date")
                except ValueError:
                    errors.append("Invalid date format. Use YYYY-MM-DD")
            
            # Rule 6: Version control
            if amendments.get('version') and amendments['version'] <= tranche.version:
                errors.append("New version must be greater than current version")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_new_tranche(grant_id, tranche_data):
        """
        Validate a new tranche before creation
        
        Args:
            grant_id: ID of the grant
            tranche_data: Dict of tranche data
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            grant = Grant.query.get(grant_id)
            if not grant:
                errors.append("Grant not found")
                return errors
            
            # Basic field validation
            if not tranche_data.get('amount'):
                errors.append("Amount is required")
            else:
                try:
                    amount = float(tranche_data['amount'])
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                except ValueError:
                    errors.append("Invalid amount format")
            
            if not tranche_data.get('expected_date'):
                errors.append("Expected date is required")
            else:
                try:
                    expected_date = datetime.strptime(tranche_data['expected_date'], '%Y-%m-%d').date()
                    if expected_date < date.today():
                        errors.append("Expected date cannot be in the past")
                    if expected_date < grant.start_date:
                        errors.append("Expected date cannot be before grant start date")
                    if expected_date > grant.end_date:
                        errors.append("Expected date cannot be after grant end date")
                except ValueError:
                    errors.append("Invalid date format. Use YYYY-MM-DD")
            
            # Budget validation
            if tranche_data.get('amount'):
                existing_tranches = Tranche.query.filter(
                    Tranche.grant_id == grant_id,
                    Tranche.status != 'archived'
                ).all()
                
                total_existing = sum(t.amount for t in existing_tranches)
                new_total = total_existing + float(tranche_data['amount'])
                
                if new_total > grant.total_budget:
                    errors.append(f"Total tranches (${new_total:,.2f}) would exceed grant budget (${grant.total_budget:,.2f})")
            
            # Trigger validation
            trigger_type = tranche_data.get('trigger_type', 'milestone')
            
            if trigger_type == 'milestone':
                milestone_id = tranche_data.get('triggering_milestone_id')
                if not milestone_id:
                    errors.append("Milestone trigger requires a valid milestone ID")
                else:
                    milestone = Milestone.query.get(milestone_id)
                    if not milestone:
                        errors.append("Specified milestone not found")
                    elif milestone.grant_id != grant_id:
                        errors.append("Milestone must belong to the same grant")
            
            elif trigger_type == 'report':
                report_type = tranche_data.get('required_report_type')
                if not report_type:
                    errors.append("Report trigger requires a valid report type")
                elif report_type not in ['financial', 'progress', 'technical']:
                    errors.append("Invalid report type. Must be: financial, progress, or technical")
            
            elif trigger_type == 'date':
                trigger_date = tranche_data.get('trigger_date')
                if not trigger_date:
                    errors.append("Date trigger requires a valid trigger date")
                else:
                    if isinstance(trigger_date, str):
                        trigger_date = datetime.strptime(trigger_date, '%Y-%m-%d').date()
                    if trigger_date < date.today():
                        errors.append("Trigger date cannot be in the past")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def get_current_tranche_values(tranche_id):
        """
        Get current values of a tranche as JSON for amendment tracking
        
        Args:
            tranche_id: ID of the tranche
            
        Returns:
            JSON string of current tranche values
        """
        tranche = Tranche.query.get(tranche_id)
        if not tranche:
            return "{}"
        
        current_values = {
            'amount': tranche.amount,
            'currency': tranche.currency,
            'description': tranche.description,
            'expected_date': tranche.expected_date.isoformat() if tranche.expected_date else None,
            'trigger_type': tranche.trigger_type,
            'triggering_milestone_id': tranche.triggering_milestone_id,
            'required_report_type': tranche.required_report_type,
            'trigger_date': tranche.trigger_date.isoformat() if tranche.trigger_date else None
        }
        
        return json.dumps(current_values)
    
    @staticmethod
    def can_edit_tranche(tranche_id):
        """
        Check if a tranche can be edited based on its status
        
        Args:
            tranche_id: ID of the tranche
            
        Returns:
            Boolean indicating if tranche can be edited
        """
        tranche = Tranche.query.get(tranche_id)
        if not tranche:
            return False
        
        # Can edit if not released or archived
        return tranche.status not in ['released', 'archived']
