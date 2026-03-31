import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from models import db, Grant, BudgetCategory, Milestone, AuditLog, FunderProfile, RuleSnapshot, ComplianceHealthScore, AuditTrail, Tranche, GrantKPI, MilestoneKPI, GrantTeam, Deliverable, Asset, Task, AssetAssignment, Notification, User
from services.compliance_service import ComplianceService
from services.effort_service import EffortService
from services.audit_service import AuditService

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

class GrantService:
    @staticmethod
    def _save_file(file_storage, subfolder=''):
        """Helper to save a file and return the filename."""
        if not file_storage or not file_storage.filename:
            return None
            
        filename = secure_filename(file_storage.filename)
        # Unique prefix to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        path = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(path, exist_ok=True)
        
        file_storage.save(os.path.join(path, unique_filename))
        return unique_filename

    @staticmethod
    def create_grant(data, files, user_id):
        """
        Creates a grant from multipart/form-data.
        :param data: dict (request.form)
        :param files: dict (request.files)
        :param user_id: int
        :return: Grant object
        """
        try:
            funder_id = data.get('funder_id')
            status = 'pending'
            rule_snapshot_id = None
            
            # 1. Handle 'Other' Funder Case
            is_other = funder_id == 'OTHER' or not funder_id
            if is_other:
                status = 'DRAFT_PENDING_RULES'
            else:
                profile = FunderProfile.query.get(int(funder_id))
                if not profile:
                    status = 'DRAFT_PENDING_RULES'
                else:
                    # Create Immutable Snapshot
                    snapshot = RuleSnapshot(
                        profile_id=profile.id,
                        rules_json=profile.rules_config,
                        created_by_user_id=user_id
                    )
                    db.session.add(snapshot)
                    db.session.flush()
                    rule_snapshot_id = snapshot.id

            # Ethics Initialization Logic
            ethics_required = data.get('ethics_required') == 'true'
            ethics_status = 'NOT_REQUIRED'
            if ethics_required:
                status = 'PENDING_ETHICS'
                ethics_status = 'PENDING_MEETING'

            grant = Grant(
                title=data.get('title'),
                funder_id=int(funder_id) if not is_other and funder_id and funder_id.isdigit() else None,
                grant_code=data.get('grant_code'),
                funder_reference_number=data.get('funder_reference_number'),
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
                total_budget=float(data.get('total_budget', 0)),
                currency=data.get('currency', 'USD'),
                exchange_rate=float(data.get('exchange_rate', 1.0)),
                financial_reporting_frequency=data.get('financial_reporting_frequency'),
                progress_reporting_frequency=data.get('progress_reporting_frequency'),
                special_requirements=data.get('special_requirements'),
                rule_snapshot_id=rule_snapshot_id,
                pi_id=user_id,
                disbursement_type=data.get('disbursement_type', 'tranches'),
                status=status,
                
                # New Ethics Fields
                ethics_required=ethics_required,
                ethics_status=ethics_status,
                ethics_approval_number=data.get('ethics_approval_number'),
                ethics_expiry_date=datetime.strptime(data.get('ethics_expiry_date'), '%Y-%m-%d').date() if data.get('ethics_expiry_date') else None
            )

            # 2. File Uploads
            grant.agreement_filename = GrantService._save_file(files.get('agreement'), 'agreements')
            grant.budget_breakdown_filename = GrantService._save_file(files.get('budget_breakdown'), 'documents')
            grant.award_letter_filename = GrantService._save_file(files.get('award_letter'), 'documents')
            grant.ethical_approval_filename = GrantService._save_file(files.get('ethical_approval'), 'documents')
            grant.reporting_template_filename = GrantService._save_file(files.get('reporting_template'), 'documents')
            
            # 3. Compliance Initialization
            if status != 'DRAFT_PENDING_RULES':
                health = ComplianceHealthScore(
                    grant_id=grant.id,
                    score=100,
                    risk_level='LOW'
                )
                db.session.add(health)
            else:
                # Notify RSU about missing profile
                rsu_admins = User.query.filter_by(role='RSU').all()
                for admin in rsu_admins:
                    db.session.add(Notification(
                        user_id=admin.id,
                        type='RULE_PROFILE_REQUIRED',
                        message=f"Action Required: Configure Rule Profile for new funder selected in {grant.title}",
                        data={'grant_id': grant.id, 'pi_id': user_id}
                    ))

            db.session.add(grant)
            db.session.flush() # Generate ID

            # 3. Budget Categories (JSON string)
            categories_json = data.get('budget_categories')
            if categories_json:
                categories = json.loads(categories_json)
                for cat in categories:
                    db.session.add(BudgetCategory(
                        grant_id=grant.id,
                        name=cat['name'],
                        allocated=float(cat['allocated'])
                    ))

            # 4. Milestones (JSON string)
            milestones_json = data.get('milestones')
            if milestones_json:
                milestones = json.loads(milestones_json)
                for i, m in enumerate(milestones):
                    milestone = Milestone(
                        grant_id=grant.id,
                        title=m['title'],
                        description=m.get('description'),
                        due_date=datetime.strptime(m['due_date'], '%Y-%m-%d').date(),
                        reporting_period=m.get('reporting_period'),
                        status=m.get('status', 'not_started'),
                        triggers_tranche=m.get('triggers_tranche'),
                        funding_amount=float(m.get('funding_amount', 0.0))
                    )
                    # Handle specific milestone evidence file (milestone_evidence_0, etc.)
                    evidence_file = files.get(f"milestone_evidence_{i}")
                    if evidence_file:
                       milestone.evidence_filename = GrantService._save_file(evidence_file, 'evidence')
                       
                    db.session.add(milestone)
                    db.session.flush() # Generate milestone ID for KPI allocation
                    
                    # 4.1. Create MilestoneKPI allocations if provided
                    kpi_allocations = m.get('kpi_allocations', [])
                    for allocation in kpi_allocations:
                        # Find the corresponding GrantKPI (match by name for now)
                        grant_kpi = None
                        for gkpi in grant.kpis if 'grant.kpis' in locals() else []:
                            if gkpi.name == allocation.get('kpiName'):
                                grant_kpi = gkpi
                                break
                        
                        if grant_kpi:
                            milestone_kpi = MilestoneKPI(
                                milestone_id=milestone.id,
                                grant_kpi_id=grant_kpi.id,
                                milestone_target=float(allocation.get('milestoneTarget', 0.0)),
                                status='PENDING'
                            )
                            db.session.add(milestone_kpi)

            # 5. Manual Tranches (JSON string)
            tranches_json = data.get('manual_tranches')
            if tranches_json:
                tranches = json.loads(tranches_json)
                for i, t in enumerate(tranches, 1):
                    db.session.add(Tranche(
                        grant_id=grant.id,
                        tranche_number=i,
                        amount=float(t['amount']),
                        currency=t.get('currency', 'USD'),
                        description=t.get('description', f'Tranche {i}'),
                        expected_date=datetime.strptime(t['expectedDate'], '%Y-%m-%d').date(),
                        trigger_type=t.get('trigger_type', 'milestone'),
                        triggering_milestone_id=t.get('triggering_milestone_id'),
                        required_report_type=t.get('required_report_type'),
                        trigger_date=datetime.strptime(t['trigger_date'], '%Y-%m-%d').date() if t.get('trigger_date') else None,
                        status=t.get('status', 'pending')
                    ))

            # 6. Grant KPIs (JSON string)
            grant_kpis_json = data.get('grant_kpis')
            if grant_kpis_json:
                kpis = json.loads(grant_kpis_json)
                for kpi_data in kpis:
                    db.session.add(GrantKPI(
                        grant_id=grant.id,
                        name=kpi_data['name'],
                        description=kpi_data.get('description', ''),
                        unit=kpi_data['unit'],
                        category=kpi_data['category'],
                        grant_wide_target=float(kpi_data['grant_wide_target']),
                        baseline_value=float(kpi_data.get('baseline_value', 0.0))
                    ))

            # 7. Audit Log
            AuditService.log_action(
                user_id=user_id,
                action='GRANT_CREATED',
                entity_type='GRANT',
                entity_id=grant.id,
                details={'status': status, 'funder_id': funder_id}
            )

            db.session.commit()
            return grant

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def approve_grant(grant_id, user_id):
        """
        Approves a pending grant.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")
        
        if grant.status == 'active':
            return grant # Already active

        grant.status = 'active'
        
        # Log Audit
        db.session.add(AuditLog(
            user_id=user_id,
            action='grant_approved',
            resource_type='grant',
            resource_id=grant.id,
            details=f'Grant "{grant.title}" approved by RSU'
        ))
        
        db.session.commit()
        return grant

    @staticmethod
    def get_grants_for_user(user_id):
        """
        Get all grants.
        - If RSU: Returns ALL grants.
        - If PI: Returns grants where they are PI.
        """
        print(f"DEBUG: get_grants_for_user called with user_id: {user_id}") # DEBUG PRINT
        # Avoid circular import
        from models import User
        user = User.query.get(user_id)
        if not user:
            print(f"DEBUG: No user found for user_id {user_id}")
            return []
            
        print(f"DEBUG: User role for user_id {user_id}: {user.role}")
        
        if user.role == 'RSU':
            grants = Grant.query.order_by(Grant.created_at.desc()).all()
        elif user.role == 'PI' or user.role == 'Co-PI':
            print(f"DEBUG: User {user_id} is PI or Co-PI.")
            from sqlalchemy import or_
            team_grants_ids = [gt.grant_id for gt in GrantTeam.query.filter_by(user_id=user_id, role='Co-PI').all()]
            print(f"DEBUG: Co-PI team grants for {user_id}: {team_grants_ids}")
            grants = Grant.query.filter(
                or_(Grant.pi_id == user_id, Grant.id.in_(team_grants_ids))
            ).order_by(Grant.created_at.desc()).all()
            print(f"DEBUG: GrantService found {len(grants)} grants for PI/Co-PI {user_id}")
        elif user.role == 'Team':
            # Get grants where user is a team member
            team_entries = GrantTeam.query.filter_by(user_id=user_id).all()
            grant_ids = [entry.grant_id for entry in team_entries]
            grants = Grant.query.filter(Grant.id.in_(grant_ids)).order_by(Grant.created_at.desc()).all()
        else:
            print(f"DEBUG: GrantService role {user.role} not handled for automated filtering")
            grants = []

        results = []
        
        for grant in grants:
            user_role = "PI" if grant.pi_id == user_id else "Co-PI"
            
            # 1. Calculate Financials
            # Defensive checks for grant values
            total_budget = float(grant.total_budget or 0.0)
            exchange_rate = float(grant.exchange_rate or 1.0)
            
            total_spent = sum((cat.spent or 0.0) for cat in grant.categories)
            remaining_budget = total_budget - total_spent
            spent_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0
            
            # Asset counting - safe iteration
            missing_assets_count = 0
            overdue_assets_count = 0
            
            # Get assets linked to this grant
            try:
                grant_assets = Asset.query.filter_by(grant_id=grant.id).all()
                missing_assets_count = sum(1 for a in grant_assets if getattr(a, 'status', '').lower() == 'missing')
                overdue_assets_count = sum(1 for a in grant_assets if getattr(a, 'status', '').lower() == 'overdue')
            except Exception as e:
                print(f"Asset count error for grant {grant.id}: {str(e)}")
            
            # 2. Find Next Deadline
            next_milestone = Milestone.query.filter(
                Milestone.grant_id == grant.id,
                Milestone.status != 'completed',
                Milestone.due_date >= datetime.today().date()
            ).order_by(Milestone.due_date.asc()).first()
            
            next_deadline_date = next_milestone.due_date if next_milestone else None
            next_deadline_label = next_milestone.title if next_milestone else "No upcoming deadlines"

            # 3. Compliance Health Score
            compliance_summary = ComplianceService.get_compliance_summary(grant.id, commit=False)

            # 4. Calculate Burn Rate (time vs spend)
            from datetime import date
            today = date.today()
            grant_start_date = grant.start_date or today
            grant_end_date = grant.end_date or today
            
            total_days = (grant_end_date - grant_start_date).days
            days_elapsed = (today - grant_start_date).days
            time_elapsed_pct = max(0.0, min(100.0, (float(days_elapsed) / float(total_days) * 100.0)) if total_days > 0 else 0.0)
            
            burn_rate_status = "normal"
            burn_rate_diff = spent_percent - time_elapsed_pct
            if burn_rate_diff > 15:
                burn_rate_status = "high"
            elif burn_rate_diff < -15:
                burn_rate_status = "low"

            # 5. Asset Integrity Check
            grant_tasks = Task.query.filter_by(grant_id=grant.id).all()
            task_ids = [t.id for t in grant_tasks]
            asset_assignments = AssetAssignment.query.filter(
                AssetAssignment.task_id.in_(task_ids)
            ).all() if task_ids else []
            total_assets = len(asset_assignments)
            returned_assets = len([a for a in asset_assignments if a.status == 'RETURNED'])
            pending_assets = total_assets - returned_assets
            asset_integrity_status = "healthy" if pending_assets == 0 else "warning" if pending_assets < 3 else "danger"

            # 6. KPI Data for Strategic Impact
            grant_kpis = GrantKPI.query.filter_by(grant_id=grant.id).all()
            kpi_summary = []
            for kpi in grant_kpis:
                kpi_summary.append({
                    'id': kpi.id,
                    'name': kpi.name,
                    'target_value': kpi.grant_wide_target,
                    'actual_value': kpi.total_actual,
                    'achievement_pct': round(kpi.achievement_pct, 1),
                    'status': kpi.status.lower(),
                    'unit': kpi.unit
                })

            # 7. Milestone Completion Rate
            all_milestones = Milestone.query.filter_by(grant_id=grant.id).all()
            completed_milestones = [m for m in all_milestones if m.status == 'completed']
            milestone_completion_rate = (len(completed_milestones) / len(all_milestones) * 100) if all_milestones else 0

            # 8. Spending Status (Effort Certification Lock)
            is_locked, lock_msg, severity = EffortService.check_spending_lock(grant.id)
            
            # 9. Audit Readiness Score & Missing Docs
            missing_docs_count = 0
            if not grant.agreement_filename:
                missing_docs_count += 1
            if not grant.award_letter_filename:
                missing_docs_count += 1
            
            # For each completed milestone, ensure there is at least one deliverable file
            for m in completed_milestones:
                has_file = False
                for d in m.deliverables:
                    if d.file_path:
                        has_file = True
                        break
                if not has_file:
                    missing_docs_count += 1
            
            asset_return_rate = (float(returned_assets) / float(total_assets) * 100.0) if total_assets > 0 else 100.0
            effort_cert_score = 100.0 if severity == "success" else 50.0 if severity == "warning" else 0.0
            audit_readiness_score = (float(spent_percent) + float(milestone_completion_rate) + asset_return_rate + effort_cert_score) / 4.0

            # 10. Format Data
            data = grant.to_dict(include_categories=True)
            data.update({
                'user_role': user_role,
                'spent_percent': spent_percent,
                'total_mwk': (grant.total_budget or 0) * (grant.exchange_rate or 1.0),
                'next_deadline_date': next_deadline_date.isoformat() if next_deadline_date else None,
                'next_deadline_label': next_deadline_label,
                'compliance_summary': compliance_summary,
                'milestone_completion_rate': round(float(milestone_completion_rate), 1),
                'audit_readiness_score': round(float(audit_readiness_score), 1),
                'missing_docs_count': missing_docs_count,
                'burn_rate': {
                    'time_elapsed_pct': round(time_elapsed_pct, 1),
                    'spend_pct': spent_percent,
                    'status': burn_rate_status,
                    'difference': round(burn_rate_diff, 1)
                },
                'asset_integrity': {
                    'total_assets': total_assets,
                    'pending_returns': pending_assets,
                    'status': asset_integrity_status
                },
                'kpi_summary': kpi_summary,
                'spending_lock': {
                    'is_locked': is_locked,
                    'message': lock_msg,
                    'severity': severity
                },
                'spending_status': {
                    'status': 'locked' if is_locked else severity if severity != 'success' else 'unlocked',
                    'text': lock_msg,
                    'is_locked': is_locked
                }
            })
            results.append(data)
            
        print(f"DEBUG: get_grants_for_user returning {len(results)} grants for user_id {user_id}")
        return results

    @staticmethod
    def get_pi_action_items(user_id):
        """
        Returns a summary of actionable items for the PI:
        - Personally custodied assets
        - Overdue team returns
        - Tranche readiness alerts
        - Pending deliverable counts
        """
        import datetime
        
        # 1. Personally Custodied Assets
        my_assets = Asset.query.filter_by(custodian_user_id=user_id).all()
        
        # 2. Overdue Team Assets
        pi_grants = Grant.query.filter_by(pi_id=user_id).all()
        co_pi_grant_ids = [gt.grant_id for gt in GrantTeam.query.filter_by(user_id=user_id, role='Co-PI').all()]
        all_pi_grant_ids = list(set([g.id for g in pi_grants] + co_pi_grant_ids))
        
        overdue_team_assets = []
        if all_pi_grant_ids:
            tasks = Task.query.filter(Task.grant_id.in_(all_pi_grant_ids)).all()
            task_ids = [t.id for t in tasks]
            if task_ids:
                assignments = AssetAssignment.query.filter(
                    AssetAssignment.task_id.in_(task_ids),
                    AssetAssignment.status != 'RETURNED'
                ).all()
                for a in assignments:
                    if a.task.status == 'completed' or (a.task.due_date and a.task.due_date < datetime.today().date()):
                        overdue_team_assets.append({
                            'id': a.id,
                            'asset_tag': a.asset.asset_tag,
                            'name': a.asset.name,
                            'task_title': a.task.title,
                            'assigned_to': a.assigned_user.name if a.assigned_user else 'Unknown',
                            'due_date': a.task.due_date.isoformat() if a.task.due_date else None
                        })

        # 3. Tranche Readiness
        ready_tranches = []
        for grant_id in all_pi_grant_ids:
            grant = Grant.query.get(grant_id)
            if not grant: continue
            for tranche in grant.tranches:
                if tranche.status == 'pending' and grant.can_release_tranche(tranche.tranche_number):
                    ready_tranches.append({
                        'grant_id': grant.id,
                        'grant_title': grant.title,
                        'tranche_number': tranche.tranche_number,
                        'amount': tranche.amount,
                        'currency': tranche.currency
                    })

        # 4. Pending Review Counts
        pending_deliverables = Deliverable.query.filter(
            Deliverable.grant_id.in_(all_pi_grant_ids),
            Deliverable.status == 'PENDING'
        ).count()

        return {
            'my_custody_assets': [a.to_dict() for a in my_assets],
            'overdue_team_assets': overdue_team_assets,
            'ready_tranches': ready_tranches,
            'pending_deliverables_count': pending_deliverables
        }

    @staticmethod
    def apply_extension(grant_id, new_end_date_str, user_id):
        """
        Logic for No-Cost Extension (NCE).
        Updates grant end_date and shifts ALL future milestones.
        """
        from models import NoCostExtension, Milestone
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")

        old_end_date = grant.end_date
        new_end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()
        
        if new_end_date <= old_end_date:
            raise ValueError("New end date must be after current end date")

        # Calculate extension delta
        delta = (new_end_date - old_end_date).days

        # 1. Update Grant
        grant.end_date = new_end_date

        # 2. Shift Milestones Linearly
        # Use a list to avoid session mutation issues if any
        future_milestones = Milestone.query.filter(
            Milestone.grant_id == grant_id,
            Milestone.status != 'COMPLETED'
        ).all()

        for m in future_milestones:
            if m.due_date:
                # Milestone due_date is DateTime in model, but stored as Date in DB often
                # We need to handle timedelta correctly
                from datetime import timedelta
                m.due_date = m.due_date + timedelta(days=delta)

        # 3. Log Audit Trail
        AuditService.log_audit_trail(
            user_id=user_id,
            action="NCE_APPROVED",
            entity_type="GRANT",
            entity_id=grant_id,
            details={
                "old_end_date": old_end_date.isoformat(),
                "new_end_date": new_end_date.isoformat(),
                "days_added": delta,
                "milestones_shifted": len(future_milestones)
            },
            is_override=True
        )

        db.session.commit()
        return grant