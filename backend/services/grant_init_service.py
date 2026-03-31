from datetime import datetime
import json
from models import db, Grant, FunderProfile, RuleSnapshot, ComplianceHealthScore, AuditTrail, Notification

class GrantInitService:
    @staticmethod
    def get_funder_list():
        """Fetches all active FunderProfile names + 'Other' option for the UI."""
        profiles = FunderProfile.query.filter_by(is_active=True).all()
        funder_list = [{'id': p.id, 'name': p.name} for p in profiles]
        funder_list.append({'id': 'OTHER', 'name': 'Other (Request New Funder)'})
        return funder_list

    @staticmethod
    def initialize_grant(data, user_id):
        """
        The Gatekeeper Logic. Ensures no grant exists without rules.
        """
        funder_id = data.get('funder_id')
        
        # 1. Handle 'Other' Funder Case
        if funder_id == 'OTHER':
            return GrantInitService._create_draft_pending_rules(data, user_id)

        # 2. Validate Funder Profile
        profile = FunderProfile.query.get(funder_id)
        if not profile:
            # Fallback to draft if profile somehow invalid
            return GrantInitService._create_draft_pending_rules(data, user_id)

        try:
            # 3. Create Grant & Rule Snapshot (Atomic Transaction)
            grant = Grant(
                title=data.get('title'),
                grant_code=data.get('grant_code'),
                funder_id=profile.id,
                pi_id=data.get('pi_id') or user_id,
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
                total_budget=float(data.get('total_budget', 0)),
                currency=data.get('currency', 'USD'),
                status='ACTIVE' # Standard activation
            )
            db.session.add(grant)
            db.session.flush()

            # 4. Create Immutable Snapshot
            snapshot = RuleSnapshot(
                grant_id=grant.id,
                profile_id=profile.id,
                rules_json=profile.rules_config,
                created_by_user_id=user_id
            )
            db.session.add(snapshot)
            grant.rule_snapshot_id = snapshot.id

            # 5. Initialize Health Score
            health = ComplianceHealthScore(
                grant_id=grant.id,
                score=100,
                risk_level='LOW'
            )
            db.session.add(health)

            # 6. Log to Audit Trail
            audit = AuditTrail(
                user_id=user_id,
                action='GRANT_INITIALIZED',
                entity_type='GRANT',
                entity_id=grant.id,
                details={'profile_name': profile.name, 'status': 'ACTIVE'}
            )
            db.session.add(audit)

            db.session.commit()
            return grant

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def _create_draft_pending_rules(data, user_id):
        """Creates a grant in DRAFT_PENDING_RULES state and notifies RSU."""
        grant = Grant(
            title=data.get('title'),
            grant_code=data.get('grant_code'),
            pi_id=user_id,
            status='DRAFT_PENDING_RULES'
        )
        db.session.add(grant)
        db.session.flush()

        # Notify RSU Admin
        rsu_admins = db.session.query(db.Model.metadata.tables['users']).filter_by(role='RSU').all()
        for admin in rsu_admins:
            notification = Notification(
                user_id=admin.id,
                type='RULE_PROFILE_REQUIRED',
                message=f"New Funder Profile Required for Grant: {grant.title}",
                data={'grant_id': grant.id, 'requested_by': user_id}
            )
            db.session.add(notification)

        db.session.commit()
        return grant
