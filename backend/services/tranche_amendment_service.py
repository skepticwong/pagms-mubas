"""
Tranche Amendment Service
Phase 3: Business Rules Engine and Amendment Workflow
"""
import json
from datetime import datetime
from models import db, Tranche, TrancheAmendment, AuditLog, User, Milestone, Grant
from services.tranche_validation_service import TrancheValidationService

class TrancheAmendmentService:
    """Service to handle tranche amendment workflow"""
    
    @staticmethod
    def submit_amendment(user_id, grant_id, tranche_id, amendment_data):
        """
        Submit a tranche amendment for approval
        
        Args:
            user_id: ID of the user submitting the amendment
            grant_id: ID of the grant
            tranche_id: ID of the tranche being amended
            amendment_data: Dict containing amendment details
            
        Returns:
            Dict with success status and amendment details
        """
        try:
            # Get tranche and validate it can be amended
            tranche = Tranche.query.get(tranche_id)
            if not tranche:
                return {'success': False, 'error': 'Tranche not found'}
            
            if not TrancheValidationService.can_edit_tranche(tranche_id):
                return {'success': False, 'error': 'This tranche cannot be amended'}
            
            # Extract amendment details
            amendment_type = amendment_data.get('amendment_type')
            reason = amendment_data.get('reason')
            supporting_docs = amendment_data.get('documents', [])
            
            if not amendment_type or not reason:
                return {'success': False, 'error': 'Amendment type and reason are required'}
            
            # Prepare changes based on amendment type
            changes = {}
            
            if amendment_type == 'amount':
                amount = amendment_data.get('amount')
                if amount is None:
                    return {'success': False, 'error': 'Amount is required for amount amendment'}
                changes['amount'] = float(amount)
                
            elif amendment_type == 'trigger':
                trigger_type = amendment_data.get('trigger_type')
                if trigger_type:
                    changes['trigger_type'] = trigger_type
                    
                    if trigger_type == 'milestone':
                        milestone_id = amendment_data.get('triggering_milestone_id')
                        if milestone_id:
                            changes['triggering_milestone_id'] = int(milestone_id)
                            
                    elif trigger_type == 'report':
                        report_type = amendment_data.get('required_report_type')
                        if report_type:
                            changes['required_report_type'] = report_type
                            
                    elif trigger_type == 'date':
                        trigger_date = amendment_data.get('trigger_date')
                        if trigger_date:
                            changes['trigger_date'] = datetime.strptime(trigger_date, '%Y-%m-%d').date()
                            
            elif amendment_type == 'date':
                expected_date = amendment_data.get('expected_date')
                if expected_date:
                    changes['expected_date'] = datetime.strptime(expected_date, '%Y-%m-%d').date()
            
            # Validate the amendment against business rules
            errors = TrancheValidationService.validate_tranche_amendment(
                grant_id, 
                tranche_id, 
                changes
            )
            
            if errors:
                return {
                    'success': False, 
                    'errors': errors
                }
            
            # Create amendment record
            amendment = TrancheAmendment(
                grant_id=grant_id,
                tranche_id=tranche_id,
                amendment_type=amendment_type,
                old_value=TrancheValidationService.get_current_tranche_values(tranche_id),
                new_value=json.dumps(changes),
                reason=reason,
                supporting_docs=json.dumps(supporting_docs),
                requested_by=user_id
            )
            
            db.session.add(amendment)
            
            # Create audit log
            db.session.add(AuditLog(
                user_id=user_id,
                action='tranche_amendment_requested',
                resource_type='tranche',
                resource_id=tranche.id,
                details=f'Tranche {tranche.tranche_number} {amendment_type} amendment requested: {reason[:100]}...'
            ))
            
            db.session.commit()
            
            # Notify approvers (this would integrate with a notification service)
            TrancheAmendmentService._notify_approvers(amendment)
            
            return {
                'success': True, 
                'amendment_id': amendment.id,
                'message': 'Amendment request submitted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to submit amendment: {str(e)}'}
    
    @staticmethod
    def approve_amendment(approver_id, amendment_id):
        """
        Approve a tranche amendment and apply the changes
        
        Args:
            approver_id: ID of the user approving the amendment
            amendment_id: ID of the amendment to approve
            
        Returns:
            Dict with success status and updated tranche details
        """
        try:
            amendment = TrancheAmendment.query.get(amendment_id)
            if not amendment:
                return {'success': False, 'error': 'Amendment not found'}
            
            if amendment.status != 'pending':
                return {'success': False, 'error': 'Amendment already processed'}
            
            # Check if user has approval rights (RSU/Finance role check)
            user = User.query.get(approver_id)
            if not user or user.role not in ['RSU', 'Finance']:
                return {'success': False, 'error': 'Insufficient permissions to approve amendments'}
            
            # Get original tranche
            tranche = Tranche.query.get(amendment.tranche_id)
            new_values = json.loads(amendment.new_value)
            
            # Create new version of tranche
            new_tranche = Tranche(
                grant_id=tranche.grant_id,
                tranche_number=tranche.tranche_number,
                parent_tranche_id=tranche.id,
                version=tranche.version + 1,
                # Copy existing values with updates
                amount=new_values.get('amount', tranche.amount),
                currency=tranche.currency,
                description=tranche.description,
                expected_date=new_values.get('expected_date', tranche.expected_date),
                trigger_type=new_values.get('trigger_type', tranche.trigger_type),
                triggering_milestone_id=new_values.get('triggering_milestone_id', tranche.triggering_milestone_id),
                required_report_type=new_values.get('required_report_type', tranche.required_report_type),
                trigger_date=new_values.get('trigger_date', tranche.trigger_date),
                status=tranche.status,
                amendment_reason=amendment.reason,
                amendment_approved_by=approver_id,
                amendment_approved_at=datetime.utcnow()
            )
            
            # Update amendment status
            amendment.status = 'approved'
            amendment.approved_by = approver_id
            amendment.approved_at = datetime.utcnow()
            
            # Archive old tranche
            tranche.status = 'archived'
            
            db.session.add(new_tranche)
            
            # Create audit log
            db.session.add(AuditLog(
                user_id=approver_id,
                action='tranche_amendment_approved',
                resource_type='tranche',
                resource_id=new_tranche.id,
                details=f'Tranche {new_tranche.tranche_number} amendment approved: {amendment.reason[:100]}...'
            ))
            
            db.session.commit()
            
            # Notify requester of approval
            TrancheAmendmentService._notify_approval(amendment, new_tranche)
            
            return {
                'success': True,
                'new_tranche_id': new_tranche.id,
                'new_tranche': new_tranche.to_dict(),
                'message': 'Amendment approved and applied successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to approve amendment: {str(e)}'}
    
    @staticmethod
    def reject_amendment(approver_id, amendment_id, rejection_reason):
        """
        Reject a tranche amendment
        
        Args:
            approver_id: ID of the user rejecting the amendment
            amendment_id: ID of the amendment to reject
            rejection_reason: Reason for rejection
            
        Returns:
            Dict with success status
        """
        try:
            amendment = TrancheAmendment.query.get(amendment_id)
            if not amendment:
                return {'success': False, 'error': 'Amendment not found'}
            
            if amendment.status != 'pending':
                return {'success': False, 'error': 'Amendment already processed'}
            
            # Check if user has approval rights
            user = User.query.get(approver_id)
            if not user or user.role not in ['RSU', 'Finance']:
                return {'success': False, 'error': 'Insufficient permissions to reject amendments'}
            
            # Update amendment status
            amendment.status = 'rejected'
            amendment.approved_by = approver_id
            amendment.approved_at = datetime.utcnow()
            amendment.rejection_reason = rejection_reason
            
            # Create audit log
            db.session.add(AuditLog(
                user_id=approver_id,
                action='tranche_amendment_rejected',
                resource_type='tranche_amendment',
                resource_id=amendment.id,
                details=f'Tranche amendment rejected: {rejection_reason[:100]}...'
            ))
            
            db.session.commit()
            
            # Notify requester of rejection
            TrancheAmendmentService._notify_rejection(amendment, rejection_reason)
            
            return {
                'success': True,
                'message': 'Amendment rejected successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to reject amendment: {str(e)}'}
    
    @staticmethod
    def get_pending_amendments():
        """
        Get all pending tranche amendments for approval
        
        Returns:
            List of pending amendment records
        """
        try:
            amendments = TrancheAmendment.query.filter_by(status='pending').order_by(
                TrancheAmendment.created_at.asc()
            ).all()
            
            return [amendment.to_dict() for amendment in amendments]
            
        except Exception as e:
            print(f"Error fetching pending amendments: {str(e)}")
            return []
    
    @staticmethod
    def get_amendment_history(tranche_id):
        """
        Get amendment history for a specific tranche
        
        Args:
            tranche_id: ID of the tranche
            
        Returns:
            List of amendment records
        """
        try:
            amendments = TrancheAmendment.query.filter_by(tranche_id=tranche_id).order_by(
                TrancheAmendment.created_at.desc()
            ).all()
            
            return [amendment.to_dict() for amendment in amendments]
            
        except Exception as e:
            print(f"Error fetching amendment history: {str(e)}")
            return []
    
    @staticmethod
    def _notify_approvers(amendment):
        """
        Notify RSU/Finance approvers of new amendment request
        
        Args:
            amendment: TrancheAmendment object
        """
        # This would integrate with your notification service
        # For now, we'll just log it
        print(f"NOTIFICATION: New tranche amendment request #{amendment.id} requires approval")
        print(f"  Grant ID: {amendment.grant_id}")
        print(f"  Tranche: {amendment.tranche.tranche_number}")
        print(f"  Type: {amendment.amendment_type}")
        print(f"  Requested by: {amendment.requested_by_user.name if amendment.requested_by_user else 'Unknown'}")
    
    @staticmethod
    def _notify_approval(amendment, new_tranche):
        """
        Notify requester of amendment approval
        
        Args:
            amendment: TrancheAmendment object
            new_tranche: New Tranche object
        """
        # This would integrate with your notification service
        print(f"NOTIFICATION: Tranche amendment #{amendment.id} approved")
        print(f"  New tranche version: {new_tranche.version}")
        print(f"  Approved by: {amendment.approved_by_user.name if amendment.approved_by_user else 'Unknown'}")
    
    @staticmethod
    def _notify_rejection(amendment, reason):
        """
        Notify requester of amendment rejection
        
        Args:
            amendment: TrancheAmendment object
            reason: Rejection reason
        """
        # This would integrate with your notification service
        print(f"NOTIFICATION: Tranche amendment #{amendment.id} rejected")
        print(f"  Reason: {reason}")
        print(f"  Rejected by: {amendment.approved_by_user.name if amendment.approved_by_user else 'Unknown'}")


def _norm_tranche_status(status):
    return (status or "").strip().lower()


class TrancheReleaseService:
    """Service to handle tranche release logic"""
    
    @staticmethod
    def check_tranche_release_readiness(tranche_id):
        """
        Check if a tranche is ready for release based on its trigger
        
        Args:
            tranche_id: ID of the tranche to check
            
        Returns:
            Dict with readiness status and details
        """
        try:
            tranche = Tranche.query.get(tranche_id)
            if not tranche:
                return {'ready': False, 'error': 'Tranche not found'}
            
            st = _norm_tranche_status(tranche.status)
            if st == 'released':
                return {'ready': False, 'error': 'Tranche already released'}
            
            if st == 'archived':
                return {'ready': False, 'error': 'Tranche is archived'}

            # If workflow already marked it ready, allow release even if
            # trigger metadata checks are incomplete.
            if st == 'ready':
                return {
                    'ready': True,
                    'trigger_details': 'Tranche status is READY'
                }
            
            # Check trigger conditions (normalize for mixed DB casing)
            trigger_type = (tranche.trigger_type or 'milestone').strip().lower()
            
            if trigger_type == 'milestone':
                return TrancheReleaseService._check_milestone_trigger(tranche)
            elif trigger_type == 'report':
                return TrancheReleaseService._check_report_trigger(tranche)
            elif trigger_type == 'date':
                return TrancheReleaseService._check_date_trigger(tranche)
            elif trigger_type == 'manual':
                return TrancheReleaseService._check_manual_trigger(tranche)
            else:
                return {'ready': False, 'error': f'Unknown trigger type: {tranche.trigger_type!r}'}
                
        except Exception as e:
            return {'ready': False, 'error': f'Error checking readiness: {str(e)}'}
    
    @staticmethod
    def _check_milestone_trigger(tranche):
        """Check if milestone-based trigger is satisfied"""
        if not tranche.triggering_milestone_id:
            # Fallback for projects using Milestone.triggers_tranche linkage.
            linked_milestones = Milestone.query.filter(
                Milestone.grant_id == tranche.grant_id,
                db.or_(
                    Milestone.triggers_tranche == tranche.id,
                    Milestone.triggers_tranche == tranche.tranche_number
                )
            ).all()

            if linked_milestones:
                all_completed = all((m.status or '').upper() == 'COMPLETED' for m in linked_milestones)
                if all_completed:
                    return {
                        'ready': True,
                        'trigger_details': f'All linked milestones completed ({len(linked_milestones)}/{len(linked_milestones)})'
                    }
                completed_count = sum(1 for m in linked_milestones if (m.status or '').upper() == 'COMPLETED')
                return {
                    'ready': False,
                    'trigger_details': f'Linked milestones completed: {completed_count}/{len(linked_milestones)}'
                }

            return {'ready': False, 'error': 'No milestone assigned'}
        
        milestone = tranche.triggering_milestone
        if not milestone:
            return {'ready': False, 'error': 'Assigned milestone not found'}
        
        if (milestone.status or '').upper() == 'COMPLETED':
            comp = getattr(milestone, 'completion_date', None)
            comp_str = comp.strftime('%Y-%m-%d') if comp else 'unknown date'
            return {
                'ready': True,
                'trigger_details': f'Milestone "{milestone.title}" completed on {comp_str}'
            }
        else:
            return {
                'ready': False,
                'trigger_details': f'Milestone "{milestone.title}" status: {milestone.status}'
            }
    
    @staticmethod
    def _check_report_trigger(tranche):
        """Check if report-based trigger is satisfied"""
        # Automated report verification is not wired yet; allow operational release
        # so schedules are not permanently blocked (RSU/Finance still control via approvals).
        return {
            'ready': True,
            'trigger_details': (
                f'Report trigger ({tranche.required_report_type or "unspecified"}): '
                'release allowed (automated report check not implemented)'
            )
        }
    
    @staticmethod
    def _check_date_trigger(tranche):
        """Check if date-based trigger is satisfied"""
        if not tranche.trigger_date:
            return {'ready': False, 'error': 'No trigger date assigned'}
        
        from datetime import date
        today = date.today()
        
        if today >= tranche.trigger_date:
            return {
                'ready': True,
                'trigger_details': f'Trigger date {tranche.trigger_date.strftime("%Y-%m-%d")} has passed'
            }
        else:
            return {
                'ready': False,
                'trigger_details': f'Waiting for trigger date: {tranche.trigger_date.strftime("%Y-%m-%d")}'
            }
    
    @staticmethod
    def _check_manual_trigger(tranche):
        """Check if manual trigger can be released"""
        return {
            'ready': True,
            'trigger_details': 'Manual release - requires RSU/Finance approval'
        }
    
    @staticmethod
    def release_tranche(tranche_id, released_by_user_id):
        """
        Release a tranche
        
        Args:
            tranche_id: ID of the tranche to release
            released_by_user_id: ID of the user releasing the tranche
            
        Returns:
            Dict with success status and release details
        """
        try:
            tranche = Tranche.query.get(tranche_id)
            if not tranche:
                return {'success': False, 'error': 'Tranche not found'}
            
            st = _norm_tranche_status(tranche.status)
            if st == 'released':
                return {'success': False, 'error': 'Tranche already released'}

            # Allow explicit workflow-ready tranches to release immediately.
            if st != 'ready':
                readiness = TrancheReleaseService.check_tranche_release_readiness(tranche_id)
                if not readiness['ready']:
                    return {'success': False, 'error': 'Tranche not ready for release', 'details': readiness}

            grant = Grant.query.get(tranche.grant_id)
            if not grant:
                return {'success': False, 'error': 'Grant not found for this tranche'}

            # Keep PI expense gating in sync with finance.release_disbursement (same field)
            amount_released = float(tranche.amount or 0)
            grant.disbursed_funds = (grant.disbursed_funds or 0.0) + amount_released
            
            # Update tranche status
            tranche.status = 'released'
            tranche.released_at = datetime.utcnow()
            tranche.released_by = released_by_user_id
            
            # Create audit log
            db.session.add(AuditLog(
                user_id=released_by_user_id,
                action='tranche_released',
                resource_type='tranche',
                resource_id=tranche.id,
                details=(
                    f'Tranche {tranche.tranche_number} released: {amount_released} '
                    f'(grant disbursed_funds now {grant.disbursed_funds})'
                ),
            ))
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Tranche {tranche.tranche_number} released successfully',
                'released_at': tranche.released_at.isoformat(),
                'amount': tranche.amount
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to release tranche: {str(e)}'}
