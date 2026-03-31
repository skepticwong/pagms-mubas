"""
Asset Service - Equipment & Asset Management
Handles CRUD operations and lifecycle management for grant assets
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Asset, AssetMaintenance, AssetTransfer, Grant, Task, User
from services.notification_service import NotificationService
from services.rule_service import RuleService
from services.asset_rules_service import AssetRulesService

class AssetService:
    """Service for managing assets and equipment"""
    
    @staticmethod
    def create_asset_request(task_id: int, request_data: Dict, user_id: int) -> tuple:
        """
        Create new asset request from task
        Returns: (asset, rule_result)
        """
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")
        
        # Validate request data
        if not request_data.get('name'):
            raise ValueError("Asset name is required")
        
        if not request_data.get('source_type'):
            raise ValueError("Source type is required")
        
        # Create asset record
        asset = Asset(
            grant_id=task.grant_id,
            name=request_data['name'],
            description=request_data.get('description', ''),
            category=request_data.get('category', 'Equipment'),
            source_type=request_data['source_type'],
            owner_name=request_data.get('owner_name'),
            custodian_user_id=user_id,
            assigned_task_id=task_id,
            acquisition_date=datetime.utcnow().date(),
            created_by_user_id=user_id
        )
        
        # Handle different source types
        if request_data['source_type'] == 'PURCHASED':
            asset.purchase_cost = request_data.get('estimated_cost', 0)
            # Generate asset tag for purchased items
            if not asset.asset_tag:
                asset.asset_tag = AssetService._generate_asset_tag(task.grant_id)
                
        elif request_data['source_type'] == 'LENDED':
            asset.expected_return_date = datetime.strptime(request_data['return_date'], '%Y-%m-%d').date() if request_data.get('return_date') else None
            asset.rental_fee_total = request_data.get('rental_fee', 0)
            asset.lending_agreement = request_data.get('lending_agreement', '')
            
        elif request_data['source_type'] == 'UNIVERSITY_OWNED':
            asset.owner_name = request_data.get('owner_name', 'MUBAS')
        
        db.session.add(asset)
        db.session.flush()  # Get ID without committing
        
        # Apply asset-specific rules engine
        rule_result = AssetRulesService.evaluate_asset_request(request_data, task.grant_id, user_id)
        
        # Handle rule outcomes
        if rule_result['outcome'] == 'BLOCK':
            db.session.rollback()
            return None, rule_result
        
        db.session.commit()
        
        # Schedule return reminders for lended assets
        if asset.source_type == 'LENDED' and asset.expected_return_date:
            AssetService._schedule_return_reminders(asset)
        
        # Send notifications if needed
        if rule_result['outcome'] == 'PRIOR_APPROVAL':
            AssetService._notify_approval_required(asset, rule_result)
        
        # Add recommendations if any
        if rule_result.get('recommendations'):
            asset.supporting_documents = asset.supporting_documents or {}
            asset.supporting_documents['recommendations'] = rule_result['recommendations']
            db.session.commit()
        
        return asset, rule_result
    
    @staticmethod
    def update_asset_status(asset_id: int, new_status: str, user_id: int, notes: str = None) -> Asset:
        """Update asset status with audit trail"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        old_status = asset.status
        asset.status = new_status
        asset.updated_at = datetime.utcnow()
        
        # Handle specific status changes
        if new_status == 'RETURNED':
            asset.actual_return_date = datetime.utcnow().date()
            # Clear custodian
            asset.custodian_user_id = None
            asset.assigned_task_id = None
            
        elif new_status == 'TRANSFERRED':
            asset.disposition_date = datetime.utcnow().date()
            asset.disposition_approved_by = user_id
            if notes:
                asset.disposition_notes = notes
            
        elif new_status == 'DISPOSED':
            asset.disposition_date = datetime.utcnow().date()
            asset.disposition_approved_by = user_id
            asset.disposition_method = notes or 'Disposed'
        
        # Create transfer record if changing custodian
        if old_status != new_status and asset.custodian_user_id != user_id:
            transfer = AssetTransfer(
                asset_id=asset_id,
                from_user_id=asset.custodian_user_id,
                to_user_id=user_id,
                reason=notes or f"Status change: {old_status} → {new_status}"
            )
            db.session.add(transfer)
        
        db.session.commit()
        return asset
    
    @staticmethod
    def get_grant_assets(grant_id: int, status_filter: str = None) -> List[Asset]:
        """Get all assets for a grant with optional status filter"""
        query = Asset.query.filter_by(grant_id=grant_id)
        if status_filter:
            query = query.filter_by(status=status_filter)
        return query.all()
    
    @staticmethod
    def get_asset_details(asset_id: int) -> Optional[Asset]:
        """Get detailed asset information including maintenance and transfers"""
        asset = Asset.query.get(asset_id)
        return asset
    
    @staticmethod
    def check_closeout_compliance(grant_id: int) -> Dict:
        """Check if all assets are properly disposed for grant closeout"""
        return AssetRulesService.check_grant_closeout_compliance(grant_id)
    
    @staticmethod
    def get_asset_compliance(asset_id: int) -> Dict:
        """Get compliance status for a specific asset"""
        return AssetRulesService.check_asset_compliance(asset_id)
    
    @staticmethod
    def get_compliance_alerts(grant_id: int = None) -> List[Dict]:
        """Get compliance alerts for assets"""
        return AssetRulesService.AssetComplianceMonitor.get_compliance_alerts(grant_id)
    
    @staticmethod
    def generate_compliance_report(grant_id: int) -> Dict:
        """Generate comprehensive compliance report for a grant"""
        return AssetRulesService.AssetComplianceMonitor.generate_compliance_report(grant_id)
    
    @staticmethod
    def get_asset_recommendations(asset_id: int) -> List[Dict]:
        """Get recommendations for asset management"""
        return AssetRulesService.get_asset_recommendations(asset_id)
    
    @staticmethod
    def create_maintenance_record(asset_id: int, maintenance_data: Dict, user_id: int) -> AssetMaintenance:
        """Create maintenance record for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        maintenance = AssetMaintenance(
            asset_id=asset_id,
            maintenance_type=maintenance_data.get('type', 'Scheduled'),
            description=maintenance_data.get('description', ''),
            cost=maintenance_data.get('cost', 0.0),
            performed_by=maintenance_data.get('performed_by', ''),
            performed_date=datetime.strptime(maintenance_data['performed_date'], '%Y-%m-%d').date() if maintenance_data.get('performed_date') else datetime.utcnow().date(),
            next_due_date=datetime.strptime(maintenance_data['next_due_date'], '%Y-%m-%d').date() if maintenance_data.get('next_due_date') else None,
            notes=maintenance_data.get('notes', ''),
            created_by_user_id=user_id
        )
        
        db.session.add(maintenance)
        
        # Update asset maintenance dates
        asset.last_maintenance_date = maintenance.performed_date
        if maintenance.next_due_date:
            asset.next_maintenance_date = maintenance.next_due_date
        
        db.session.commit()
        return maintenance
    
    @staticmethod
    def get_upcoming_maintenance(grant_id: int, days_ahead: int = 30) -> List[Asset]:
        """Get assets with upcoming maintenance"""
        cutoff_date = datetime.utcnow().date() + timedelta(days=days_ahead)
        
        assets = Asset.query.filter(
            Asset.grant_id == grant_id,
            Asset.next_maintenance_date <= cutoff_date,
            Asset.status == 'ACTIVE'
        ).all()
        
        return assets
    
    @staticmethod
    def get_overdue_returns(grant_id: int = None) -> List[Asset]:
        """Get assets with overdue return dates"""
        query = Asset.query.filter(
            Asset.expected_return_date < datetime.utcnow().date(),
            Asset.status.in_(['ACTIVE', 'LENDED'])
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        return query.all()
    
    @staticmethod
    def transfer_asset(asset_id: int, from_user_id: int, to_user_id: int, reason: str, approved_by: int) -> AssetTransfer:
        """Transfer asset custody"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Create transfer record
        transfer = AssetTransfer(
            asset_id=asset_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reason=reason,
            approved_by=approved_by
        )
        
        # Update asset custodian
        asset.custodian_user_id = to_user_id
        asset.updated_at = datetime.utcnow()
        
        db.session.add(transfer)
        db.session.commit()
        
        return transfer
    
    # Private helper methods
    
    @staticmethod
    def _generate_asset_tag(grant_id: int) -> str:
        """Generate unique asset tag for grant"""
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")
        
        # Use grant code + sequential number
        asset_count = Asset.query.filter_by(grant_id=grant_id).count()
        return f"{grant.grant_code}-ASSET-{asset_count + 1:03d}"
    
    @staticmethod
    def _schedule_return_reminders(asset: Asset):
        """Schedule return reminders for lended assets"""
        if not asset.expected_return_date:
            return
        
        # Schedule reminders 7 days and 1 day before return
        reminder_dates = [
            asset.expected_return_date - timedelta(days=7),
            asset.expected_return_date - timedelta(days=1)
        ]
        
        for reminder_date in reminder_dates:
            if reminder_date > datetime.utcnow().date():
                # In production, this would integrate with a job scheduler
                # For now, we'll just log that a reminder should be sent
                print(f"Reminder scheduled: Asset {asset.name} due on {asset.expected_return_date}")
    
    @staticmethod
    def _notify_approval_required(asset: Asset, rule_result: Dict):
        """Notify stakeholders about approval requirements"""
        # In production, this would send actual notifications
        print(f"Approval required for asset: {asset.name}")
        print(f"Reasons: {rule_result.get('prior_approval_reasons', [])}")
    
    @staticmethod
    def get_asset_statistics(grant_id: int) -> Dict:
        """Get asset statistics for a grant"""
        total_assets = Asset.query.filter_by(grant_id=grant_id).count()
        
        # Count by status
        status_counts = {}
        statuses = ['ACTIVE', 'IN_REPAIR', 'RETURNED', 'TRANSFERRED', 'DISPOSED', 'LENDED']
        for status in statuses:
            count = Asset.query.filter_by(grant_id=grant_id, status=status).count()
            if count > 0:
                status_counts[status] = count
        
        # Count by source type
        source_counts = {}
        sources = ['PURCHASED', 'LENDED', 'UNIVERSITY_OWNED']
        for source in sources:
            count = Asset.query.filter_by(grant_id=grant_id, source_type=source).count()
            if count > 0:
                source_counts[source] = count
        
        # Total value
        total_value = db.session.query(db.func.sum(Asset.purchase_cost)).filter_by(grant_id=grant_id).scalar() or 0
        
        # Overdue returns
        overdue_count = len(AssetService.get_overdue_returns(grant_id))
        
        return {
            'total_assets': total_assets,
            'status_breakdown': status_counts,
            'source_breakdown': source_counts,
            'total_value': total_value,
            'overdue_returns': overdue_count
        }
