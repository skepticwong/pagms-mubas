# backend/ethics_watchdog.py
import os
from datetime import datetime, timedelta
from app import app
from models import db, Grant, EthicsSuspensionPeriod, Notification, User
from services.audit_service import AuditService

def run_ethics_watchdog():
    """
    Nightly watchdog to monitor ethics certificate expiration.
    - Marks expired grants as SUSPENDED
    - Creates EthicsSuspensionPeriod records (with correct field names)
    - Sends 30-day advance warnings
    """
    with app.app_context():
        print(f"[{datetime.now()}] Starting Ethics Watchdog...")

        today = datetime.utcnow().date()
        warning_date = today + timedelta(days=30)

        # 1. Find grants needing ethics that are NOT already suspended or expired
        active_ethics_grants = Grant.query.filter(
            Grant.ethics_required == True,
            Grant.ethics_status.in_(['VERIFIED', 'PENDING_ETHICS'])
        ).all()

        for grant in active_ethics_grants:
            if not grant.ethics_expiry_date:
                continue

            expiry_date = grant.ethics_expiry_date

            # Case A: Expired Today → Suspend
            if expiry_date <= today:
                print(f"!! Grant {grant.grant_code} ethics EXPIRED on {expiry_date}")

                old_ethics_status = grant.ethics_status
                grant.ethics_status = 'EXPIRED'
                grant.status = 'ETHICS_SUSPENDED'  # Gap 4 fix: lock the grant

                # ── Gap 4 fix: Use correct model field names ─────────────────
                suspension = EthicsSuspensionPeriod(
                    grant_id=grant.id,
                    suspended_at=datetime.utcnow(),          # was: suspension_date (wrong)
                    suspension_reason=f"Ethics certificate expired on {expiry_date}."  # was: reason (wrong)
                )
                db.session.add(suspension)

                # Audit Log
                AuditService.log_action(
                    user_id=0,  # System action
                    action='ETHICS_EXPIRED_SUSPENDED',
                    entity_type='GRANT',
                    entity_id=grant.id,
                    details={
                        'expiry_date': str(expiry_date),
                        'previous_ethics_status': old_ethics_status,
                        'grant_status_changed_to': 'ETHICS_SUSPENDED'
                    }
                )

                # Notify PI
                pi = User.query.get(grant.pi_id)
                if pi:
                    notif = Notification(
                        user_id=pi.id,
                        title="URGENT: Grant Suspended — Ethics Certificate Expired",
                        message=(
                            f"The ethics certificate for grant {grant.grant_code} expired on {expiry_date}. "
                            f"Financial and task modules are LOCKED. "
                            f"Please upload a renewed certificate immediately to reinstate the grant."
                        ),
                        type='statusCritical'
                    )
                    db.session.add(notif)

                db.session.commit()

            # Case B: Expiring within 30 days → Advance Warning
            elif expiry_date <= warning_date:
                days_left = (expiry_date - today).days
                print(f"?? Grant {grant.grant_code} ethics EXPIRING SOON on {expiry_date} ({days_left}d left)")

                pi = User.query.get(grant.pi_id)
                if pi:
                    notif = Notification(
                        user_id=pi.id,
                        title=f"Ethics Expiry Warning — {days_left} Days Left",
                        message=(
                            f"The ethics certificate for grant {grant.grant_code} will expire on {expiry_date}. "
                            f"Please prepare a renewal to avoid grant suspension."
                        ),
                        type='statusWarn'
                    )
                    db.session.add(notif)

                db.session.commit()

        print(f"[{datetime.now()}] Ethics Watchdog finished.")

if __name__ == "__main__":
    run_ethics_watchdog()


