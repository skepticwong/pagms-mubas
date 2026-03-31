import json
from datetime import datetime
from models import db, Grant, Rule, FunderProfile, RuleSnapshot

class RuleVersionService:
    @staticmethod
    def snapshot_on_approval(grant_id, user_id):
        """
        Creates a permanent snapshot of the active rule profile for a grant.
        Called when RSU approves a grant.
        """
        grant = Grant.query.get(grant_id)
        if not grant or not grant.rule_profile_id:
            return None

        profile = FunderProfile.query.get(grant.rule_profile_id)
        if not profile:
            return None

        # Fetch all active rules in the profile and serialize them
        rules_data = []
        for rule in profile.rules:
            if rule.is_active:
                rules_data.append(rule.to_dict())

        snapshot = RuleSnapshot(
            grant_id=grant_id,
            rule_profile_id=profile.id,
            snapshot_data=json.dumps(rules_data),
            snapped_at=datetime.utcnow(),
            snapped_by_id=user_id
        )
        
        db.session.add(snapshot)
        db.session.flush() # Get ID
        
        grant.rule_snapshot_id = snapshot.id
        db.session.commit()
        
        return snapshot.id

    @staticmethod
    def create_new_rule_version(rule_id, updated_data, user_id):
        """
        Instead of updating a rule, we deactivate the old one and create a new version.
        This ensures snapshots remain valid reference points.
        """
        old_rule = Rule.query.get(rule_id)
        if not old_rule:
            return None

        # Deactivate old version
        old_rule.is_active = False
        old_rule.valid_to = datetime.utcnow()

        # Create new version
        new_rule = Rule(
            name=updated_data.get('name', old_rule.name),
            rule_type=updated_data.get('rule_type', old_rule.rule_type),
            logic_config=json.dumps(updated_data.get('logic_config', json.loads(old_rule.logic_config))),
            outcome=updated_data.get('outcome', old_rule.outcome),
            priority_level=updated_data.get('priority_level', old_rule.priority_level),
            version_number=old_rule.version_number + 1,
            guidance_text=updated_data.get('guidance_text', old_rule.guidance_text),
            created_by_id=user_id,
            is_active=True
        )
        
        db.session.add(new_rule)
        
        # Link to same profiles
        for profile in old_rule.profiles:
            profile.rules.append(new_rule)
        
        db.session.commit()
        return new_rule
