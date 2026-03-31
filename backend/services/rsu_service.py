# backend/services/rsu_service.py
from datetime import datetime
from models import db, Grant, EthicsSuspensionPeriod, AuditLog, Notification
from services.audit_service import AuditService

class RSUService:
    @staticmethod
    def verify_ethics_certificate(grant_id, user_id, approval_number=None, expiry_date=None, notes=None):
        """
        Verify/reinstate the ethics certificate for a grant.
        - Sets ethics_status → VERIFIED
        - Restores Grant.status → ACTIVE (Gap 2 fix)
        - Closes all open suspension periods with reinstated_at + reinstated_by (Gap 1 fix)
        - Logs the full suspension window in the AuditTrail (Gap 6 fix)
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")

        # Update certificate details if provided
        if approval_number:
            grant.ethics_approval_number = approval_number
        if expiry_date:
            if isinstance(expiry_date, str):
                grant.ethics_expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            else:
                grant.ethics_expiry_date = expiry_date

        old_ethics_status = grant.ethics_status
        old_grant_status = grant.status

        # ── Gap 2 fix: Restore grant.status to ACTIVE ──────────────────────────
        grant.ethics_status = 'VERIFIED'
        if grant.status in ('ETHICS_SUSPENDED', 'SUSPENDED', 'SUSPENDED_ETHICS'):
            grant.status = 'ACTIVE'

        # ── Gap 1 fix: Close open suspension periods with correct field names ──
        reinstatement_time = datetime.utcnow()
        open_suspensions = EthicsSuspensionPeriod.query.filter_by(
            grant_id=grant_id, reinstated_at=None
        ).all()

        suspension_audit_records = []
        for suspension in open_suspensions:
            suspension.reinstated_at = reinstatement_time
            suspension.reinstated_by = user_id
            suspension.reinstatement_notes = notes

            # Collect details for audit trail (Gap 6)
            suspension_audit_records.append({
                'suspension_id': suspension.id,
                'suspension_start': suspension.suspended_at.isoformat() if suspension.suspended_at else None,
                'suspension_end': reinstatement_time.isoformat(),
                'duration_days': (reinstatement_time - suspension.suspended_at).days if suspension.suspended_at else None,
                'reason': suspension.suspension_reason
            })

        # ── Gap 6 fix: Audit trail includes full suspension window ─────────────
        AuditService.log_action(
            user_id=user_id,
            action='ETHICS_VERIFIED',
            entity_type='GRANT',
            entity_id=grant_id,
            details={
                'previous_ethics_status': old_ethics_status,
                'previous_grant_status': old_grant_status,
                'new_grant_status': grant.status,
                'new_expiry_date': grant.ethics_expiry_date.isoformat() if grant.ethics_expiry_date else None,
                'approval_number': grant.ethics_approval_number,
                'notes': notes,
                'suspension_periods_closed': suspension_audit_records  # Critical for reporting gaps
            }
        )

        # Notify PI — include suspension duration if applicable
        total_suspended_days = sum(r['duration_days'] for r in suspension_audit_records if r['duration_days'])
        duration_note = f" The grant was suspended for {total_suspended_days} day(s)." if total_suspended_days else ""

        notification = Notification(
            user_id=grant.pi_id,
            title="Ethics Certificate Verified — Grant Reinstated",
            message=(
                f"The ethics certificate for grant {grant.grant_code} has been verified by RSU. "
                f"All modules are now unlocked and the grant is ACTIVE.{duration_note}"
            ),
            type='success'
        )
        db.session.add(notification)

        db.session.commit()
        return grant

    @staticmethod
    def reject_ethics_certificate(grant_id, user_id, reason):
        """
        Reject an ethics certificate submission.
        Ethics status returns to PENDING_ETHICS for re-upload.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")

        grant.ethics_status = 'PENDING_ETHICS'

        notification = Notification(
            user_id=grant.pi_id,
            title="Ethics Certificate Rejected",
            message=(
                f"RSU has rejected the ethics certificate for grant {grant.grant_code}. "
                f"Reason: {reason}. Please upload a corrected certificate."
            ),
            type='statusCritical'
        )
        db.session.add(notification)

        AuditService.log_action(
            user_id=user_id,
            action='ETHICS_REJECTED',
            entity_type='GRANT',
            entity_id=grant_id,
            details={'reason': reason, 'grant_status': grant.status}
        )

        db.session.commit()
        return grant

    @staticmethod
    def get_pending_ethics_grants():
        """
        Get all grants pending ethics action by RSU.
        Includes fresh submissions, renewals after expiry, and suspended grants.
        """
        return Grant.query.filter(
            Grant.ethics_required == True,
            Grant.ethics_status.in_(['PENDING_ETHICS', 'PENDING_MEETING', 'SUSPENDED_ETHICS', 'EXPIRED'])
        ).all()
