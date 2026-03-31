"""
NCE Service - No-Cost Extension workflow management
Handles formal time extension requests with validation and approval workflow
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Grant, GrantAmendment, User, Milestone, Task
from services.notification_service import NotificationService
from services.rule_service import RuleService

class NCEService:
    """Service for managing No-Cost Extension requests and workflows"""
    
    @staticmethod
    def request_extension(grant_id: int, requested_end_date: str, justification: str, 
                        user_id: int, supporting_docs: List[str] = None) -> Dict:
        """
        Submit a new NCE request
        """
        grant = Grant.query.get_or_404(grant_id)
        
        # Validation checks
        validation_result = NCEService._validate_nce_request(grant, requested_end_date, user_id)
        if not validation_result['valid']:
            return {
                'success': False,
                'errors': validation_result['errors'],
                'warnings': validation_result.get('warnings', [])
            }
        
        # Calculate extension days
        current_end = grant.end_date
        new_end = datetime.strptime(requested_end_date, '%Y-%m-%d').date()
        extension_days = (new_end - current_end).days
        
        # Create amendment record
        amendment = GrantAmendment(
            grant_id=grant_id,
            amendment_type='NCE',
            title=f"No-Cost Extension Request - {extension_days} days",
            description=f"Request to extend grant end date from {current_end} to {new_end}",
            current_end_date=current_end,
            requested_new_end_date=new_end,
            extension_days=extension_days,
            justification=justification,
            supporting_docs=supporting_docs or [],
            requested_by=user_id,
            status='PENDING'
        )
        
        db.session.add(amendment)
        db.session.commit()
        
        # Apply rules engine validation
        rule_context = {
            'amendment_type': 'NCE',
            'extension_days': extension_days,
            'justification': justification,
            'grant_progress': grant.project_progress_percentage
        }
        
        rule_result = RuleService.evaluate_action('NCE_REQUEST', rule_context, grant_id, commit=False)
        
        # Notify RSU
        try:
            NotificationService.notify_rsu_staff(
                'NCE_REQUESTED',
                {
                    'grant_id': grant_id,
                    'grant_title': grant.title,
                    'pi_name': grant.pi.name,
                    'extension_days': extension_days,
                    'current_end_date': current_end.isoformat(),
                    'requested_end_date': new_end.isoformat(),
                    'amendment_id': amendment.id,
                    'justification': justification
                }
            )
        except Exception as e:
            print(f"Notification error: {e}")
        
        return {
            'success': True,
            'amendment': amendment.to_dict(),
            'rule_evaluation': rule_result,
            'warnings': validation_result.get('warnings', [])
        }
    
    @staticmethod
    def _validate_nce_request(grant: Grant, requested_end_date: str, user_id: int) -> Dict:
        """Validate NCE request against business rules"""
        errors = []
        warnings = []
        
        # Check if user is PI or authorized
        if grant.pi_id != user_id:
            # Add role-based permission check here if needed
            has_permission = False  # Placeholder for role check
            if not has_permission:
                errors.append("Only the Principal Investigator can request extensions")
        
        # Check if there's already a pending NCE
        pending_nce = GrantAmendment.query.filter_by(
            grant_id=grant.id,
            amendment_type='NCE',
            status='PENDING'
        ).first()
        
        if pending_nce:
            errors.append("An extension request is already pending for this grant")
        
        # Validate date
        try:
            new_end_date = datetime.strptime(requested_end_date, '%Y-%m-%d').date()
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD")
            return {'valid': False, 'errors': errors}
        
        # Check if new date is after current end date
        if new_end_date <= grant.end_date:
            errors.append("New end date must be after current end date")
        
        # Check if extension is reasonable (not more than 1 year)
        max_extension = timedelta(days=365)
        if new_end_date - grant.end_date > max_extension:
            errors.append("Extension cannot exceed 365 days")
        
        # Check for overdue reports
        try:
            # Skip ProgressReport check as the model doesn't exist
            # This check can be added later if ProgressReport model is implemented
            pass
        except:
            # If ProgressReport table doesn't exist or has issues, skip this check
            pass
        
        # Check grant progress
        progress = grant.project_progress_percentage
        if progress < 25:
            warnings.append("Grant progress is less than 25%. Extension may require additional justification")
        
        # Check if grant is active
        if grant.status not in ['active', 'pending']:
            warnings.append(f"Grant status is '{grant.status}'. Extension may not be appropriate.")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def approve_extension(amendment_id: int, approver_id: int, notes: str = None, 
                         shift_milestones: bool = True) -> Dict:
        """Approve an NCE request and update grant end date"""
        amendment = GrantAmendment.query.get_or_404(amendment_id)
        
        if amendment.status != 'PENDING':
            return {'success': False, 'error': 'Amendment is not in pending status'}
        
        grant = amendment.grant
        
        # Update grant end date
        old_end_date = grant.end_date
        grant.end_date = amendment.requested_new_end_date
        
        # Update amendment
        amendment.status = 'APPROVED'
        amendment.approved_by = approver_id
        amendment.approved_at = datetime.utcnow()
        if notes:
            amendment.description += f"\n\nApproval Notes: {notes}"
        
        # Optionally shift milestones
        if shift_milestones:
            shifted_count = NCEService._shift_milestones(grant, old_end_date, amendment.requested_new_end_date)
            if shifted_count > 0:
                amendment.description += f"\n\n{shifted_count} milestones/tasks shifted proportionally."
        
        db.session.commit()
        
        # Notify PI
        try:
            NotificationService.notify_rule_event(
                grant.pi_id,
                'NCE_APPROVED',
                {
                    'grant_id': grant.id,
                    'old_end_date': old_end_date.isoformat(),
                    'new_end_date': grant.end_date.isoformat(),
                    'extension_days': amendment.extension_days,
                    'approved_by': approver_id,
                    'notes': notes
                }
            )
        except Exception as e:
            print(f"Notification error: {e}")
        
        return {
            'success': True,
            'amendment': amendment.to_dict(),
            'grant': grant.to_dict()
        }
    
    @staticmethod
    def reject_extension(amendment_id: int, rejecter_id: int, rejection_reason: str) -> Dict:
        """Reject an NCE request"""
        amendment = GrantAmendment.query.get_or_404(amendment_id)
        
        if amendment.status != 'PENDING':
            return {'success': False, 'error': 'Amendment is not in pending status'}
        
        amendment.status = 'REJECTED'
        amendment.rejected_by = rejecter_id
        amendment.rejected_at = datetime.utcnow()
        amendment.description += f"\n\nRejection Reason: {rejection_reason}"
        
        db.session.commit()
        
        # Notify PI
        try:
            NotificationService.notify_rule_event(
                amendment.grant.pi_id,
                'NCE_REJECTED',
                {
                    'grant_id': amendment.grant_id,
                    'rejection_reason': rejection_reason,
                    'rejected_by': rejecter_id
                }
            )
        except Exception as e:
            print(f"Notification error: {e}")
        
        return {
            'success': True,
            'amendment': amendment.to_dict()
        }
    
    @staticmethod
    def _shift_milestones(grant: Grant, old_end_date: datetime.date, new_end_date: datetime.date) -> int:
        """Proportionally shift milestone and task due dates"""
        if not old_end_date or not new_end_date:
            return 0
        
        extension_days = (new_end_date - old_end_date).days
        total_days = (old_end_date - grant.start_date).days
        shift_ratio = extension_days / total_days if total_days > 0 else 0
        
        shifted_count = 0
        
        # Shift milestones
        try:
            for milestone in grant.milestones_list:
                if milestone.due_date and milestone.status != 'COMPLETED':
                    # Calculate shift for this milestone
                    days_from_start = (milestone.due_date - grant.start_date).days
                    shift_days = int(days_from_start * shift_ratio)
                    milestone.due_date = milestone.due_date + timedelta(days=shift_days)
                    shifted_count += 1
        except:
            # If milestones relationship doesn't exist, skip
            pass
        
        # Shift tasks
        try:
            for task in grant.tasks_list:
                if task.due_date and task.status != 'COMPLETED':
                    days_from_start = (task.due_date - grant.start_date).days
                    shift_days = int(days_from_start * shift_ratio)
                    task.due_date = task.due_date + timedelta(days=shift_days)
                    shifted_count += 1
        except:
            # If tasks relationship doesn't exist, skip
            pass
        
        return shifted_count
    
    @staticmethod
    def get_pending_amendments() -> List[GrantAmendment]:
        """Get all pending amendments for RSU review"""
        return GrantAmendment.query.filter_by(status='PENDING').order_by(GrantAmendment.requested_at.desc()).all()
    
    @staticmethod
    def get_grant_amendments(grant_id: int) -> List[GrantAmendment]:
        """Get all amendments for a specific grant"""
        return GrantAmendment.query.filter_by(grant_id=grant_id).order_by(GrantAmendment.created_at.desc()).all()
    
    @staticmethod
    def get_amendment_details(amendment_id: int) -> Optional[GrantAmendment]:
        """Get detailed amendment information"""
        return GrantAmendment.query.get(amendment_id)
    
    @staticmethod
    def withdraw_request(amendment_id: int, user_id: int) -> Dict:
        """Withdraw a pending amendment request"""
        amendment = GrantAmendment.query.get_or_404(amendment_id)
        
        if amendment.status != 'PENDING':
            return {'success': False, 'error': 'Only pending requests can be withdrawn'}
        
        if amendment.requested_by != user_id:
            return {'success': False, 'error': 'Only the requester can withdraw the request'}
        
        amendment.status = 'WITHDRAWN'
        amendment.description += f"\n\nRequest withdrawn by user on {datetime.utcnow().date()}"
        
        db.session.commit()
        
        return {
            'success': True,
            'amendment': amendment.to_dict()
        }
    
    @staticmethod
    def get_extension_statistics() -> Dict:
        """Get statistics about NCE requests"""
        total_requests = GrantAmendment.query.filter_by(amendment_type='NCE').count()
        pending_requests = GrantAmendment.query.filter_by(amendment_type='NCE', status='PENDING').count()
        approved_requests = GrantAmendment.query.filter_by(amendment_type='NCE', status='APPROVED').count()
        rejected_requests = GrantAmendment.query.filter_by(amendment_type='NCE', status='REJECTED').count()
        
        # Average extension days for approved requests
        approved_amendments = GrantAmendment.query.filter_by(amendment_type='NCE', status='APPROVED').all()
        avg_extension_days = 0
        if approved_amendments:
            avg_extension_days = sum(a.extension_days or 0 for a in approved_amendments) / len(approved_amendments)
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_requests = GrantAmendment.query.filter(
            GrantAmendment.amendment_type == 'NCE',
            GrantAmendment.requested_at >= thirty_days_ago
        ).count()
        
        return {
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
            'average_extension_days': round(avg_extension_days, 1),
            'recent_requests': recent_requests,
            'approval_rate': round((approved_requests / total_requests * 100) if total_requests > 0 else 0, 1)
        }
