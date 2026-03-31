"""
Asset Transfer Service - Asset custody transfer management
Handles asset transfers, approvals, and audit trails
"""

from datetime import datetime
from typing import Dict, List, Optional
from models import db, Asset, AssetTransfer, User, Grant
from services.notification_service import NotificationService

class AssetTransferService:
    """Service for managing asset transfers and custody changes"""
    
    @staticmethod
    def initiate_transfer(asset_id: int, from_user_id: int, to_user_id: int, reason: str, initiated_by: int) -> AssetTransfer:
        """Initiate an asset transfer request"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Validate asset can be transferred
        if asset.status not in ['ACTIVE', 'IN_REPAIR']:
            raise ValueError(f"Asset with status '{asset.status}' cannot be transferred")
        
        # Validate users
        from_user = User.query.get(from_user_id) if from_user_id else None
        to_user = User.query.get(to_user_id)
        if not to_user:
            raise ValueError("Target user not found")
        
        # Check if current custodian matches from_user
        if asset.custodian_user_id and asset.custodian_user_id != from_user_id:
            raise ValueError("Asset is not currently assigned to the specified user")
        
        # Create transfer record
        transfer = AssetTransfer(
            asset_id=asset_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reason=reason,
            approved_by=initiated_by  # For self-transfers, the initiator can approve
        )
        
        db.session.add(transfer)
        db.session.flush()
        
        # Update asset custody
        asset.custodian_user_id = to_user_id
        asset.updated_at = datetime.utcnow()
        
        # Create notification for recipient
        NotificationService.create_notification(
            user_id=to_user_id,
            title=f"Asset Received: {asset.name}",
            message=f"You have been assigned custody of {asset.name} (Tag: {asset.asset_tag or 'N/A'}). Reason: {reason}",
            type='asset_transfer',
            related_id=asset_id
        )
        
        # Create notification for sender if different from recipient
        if from_user_id and from_user_id != to_user_id:
            NotificationService.create_notification(
                user_id=from_user_id,
                title=f"Asset Transferred: {asset.name}",
                message=f"Asset {asset.name} has been transferred to {to_user.name}. Reason: {reason}",
                type='asset_transfer',
                related_id=asset_id
            )
        
        db.session.commit()
        
        return transfer
    
    @staticmethod
    def request_transfer_approval(asset_id: int, from_user_id: int, to_user_id: int, reason: str, requested_by: int) -> AssetTransfer:
        """Request asset transfer that requires approval"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Check if approval is required (high-value assets or cross-grant transfers)
        approval_required = AssetTransferService._requires_approval(asset, from_user_id, to_user_id)
        
        transfer = AssetTransfer(
            asset_id=asset_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reason=reason
            # approved_by will be set when approved
        )
        
        db.session.add(transfer)
        db.session.flush()
        
        if approval_required:
            # Don't update custody until approved
            # Create approval request notification
            approvers = AssetTransferService._get_approvers(asset)
            
            for approver in approvers:
                NotificationService.create_notification(
                    user_id=approver.id,
                    title=f"Asset Transfer Approval Required",
                    message=f"Transfer request for {asset.name} from {User.query.get(from_user_id).name if from_user_id else 'Unassigned'} to {User.query.get(to_user_id).name}. Reason: {reason}",
                    type='transfer_approval',
                    related_id=transfer.id
                )
        else:
            # Auto-approve for low-value transfers
            transfer.approved_by = requested_by
            asset.custodian_user_id = to_user_id
            asset.updated_at = datetime.utcnow()
            
            # Create notifications
            NotificationService.create_notification(
                user_id=to_user_id,
                title=f"Asset Received: {asset.name}",
                message=f"You have been assigned custody of {asset.name}. Reason: {reason}",
                type='asset_transfer',
                related_id=asset_id
            )
        
        db.session.commit()
        return transfer
    
    @staticmethod
    def approve_transfer(transfer_id: int, approved_by: int, notes: str = None) -> AssetTransfer:
        """Approve a pending asset transfer"""
        transfer = AssetTransfer.query.get(transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        
        if transfer.approved_by:
            raise ValueError("Transfer has already been approved")
        
        # Approve the transfer
        transfer.approved_by = approved_by
        transfer.transfer_date = datetime.utcnow()
        
        # Update asset custody
        asset = transfer.asset
        asset.custodian_user_id = transfer.to_user_id
        asset.updated_at = datetime.utcnow()
        
        # Create notifications
        NotificationService.create_notification(
            user_id=transfer.to_user_id,
            title=f"Asset Transfer Approved: {asset.name}",
            message=f"Your transfer request for {asset.name} has been approved.",
            type='asset_transfer',
            related_id=asset.id
        )
        
        NotificationService.create_notification(
            user_id=transfer.from_user_id,
            title=f"Asset Transferred: {asset.name}",
            message=f"Asset {asset.name} has been transferred to {transfer.to_user.name}.",
            type='asset_transfer',
            related_id=asset.id
        )
        
        db.session.commit()
        return transfer
    
    @staticmethod
    def reject_transfer(transfer_id: int, rejected_by: int, rejection_reason: str) -> AssetTransfer:
        """Reject a pending asset transfer"""
        transfer = AssetTransfer.query.get(transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        
        if transfer.approved_by:
            raise ValueError("Transfer has already been approved")
        
        # Create rejection record (we'll use a special transfer record for rejections)
        rejection = AssetTransfer(
            asset_id=transfer.asset_id,
            from_user_id=transfer.from_user_id,
            to_user_id=transfer.to_user_id,
            reason=f"REJECTED: {transfer.reason} | Rejection: {rejection_reason}",
            approved_by=rejected_by,
            transfer_date=datetime.utcnow()
        )
        
        db.session.add(rejection)
        
        # Create notifications
        NotificationService.create_notification(
            user_id=transfer.to_user_id,
            title=f"Asset Transfer Rejected: {transfer.asset.name}",
            message=f"Your transfer request for {transfer.asset.name} has been rejected. Reason: {rejection_reason}",
            type='transfer_rejection',
            related_id=transfer.asset.id
        )
        
        NotificationService.create_notification(
            user_id=transfer.from_user_id,
            title=f"Asset Transfer Rejected: {transfer.asset.name}",
            message=f"Transfer request for {transfer.asset.name} has been rejected.",
            type='transfer_rejection',
            related_id=transfer.asset.id
        )
        
        db.session.commit()
        return rejection
    
    @staticmethod
    def get_pending_transfers(grant_id: int = None, user_id: int = None) -> List[Dict]:
        """Get pending transfer requests"""
        query = AssetTransfer.query.filter(AssetTransfer.approved_by.is_(None))
        
        if grant_id:
            query = query.join(Asset).filter(Asset.grant_id == grant_id)
        
        if user_id:
            query = query.filter(
                (AssetTransfer.from_user_id == user_id) | 
                (AssetTransfer.to_user_id == user_id)
            )
        
        transfers = query.order_by(AssetTransfer.created_at.desc()).all()
        
        pending_transfers = []
        for transfer in transfers:
            pending_transfers.append({
                'transfer': transfer.to_dict(),
                'asset': transfer.asset.to_dict(),
                'from_user': transfer.from_user.to_dict() if transfer.from_user else None,
                'to_user': transfer.to_user.to_dict() if transfer.to_user else None,
                'requires_approval': AssetTransferService._requires_approval(
                    transfer.asset, transfer.from_user_id, transfer.to_user_id
                )
            })
        
        return pending_transfers
    
    @staticmethod
    def get_transfer_history(asset_id: int = None, grant_id: int = None) -> List[Dict]:
        """Get transfer history"""
        query = AssetTransfer.query
        
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
        elif grant_id:
            query = query.join(Asset).filter(Asset.grant_id == grant_id)
        
        transfers = query.order_by(AssetTransfer.created_at.desc()).all()
        
        history = []
        for transfer in transfers:
            history.append({
                'transfer': transfer.to_dict(),
                'asset': transfer.asset.to_dict(),
                'from_user': transfer.from_user.to_dict() if transfer.from_user else None,
                'to_user': transfer.to_user.to_dict() if transfer.to_user else None,
                'approver': transfer.approver.to_dict() if transfer.approver else None
            })
        
        return history
    
    @staticmethod
    def get_user_assets(user_id: int) -> List[Dict]:
        """Get assets currently assigned to a user"""
        assets = Asset.query.filter_by(custodian_user_id=user_id, status='ACTIVE').all()
        
        user_assets = []
        for asset in assets:
            # Get latest transfer
            latest_transfer = AssetTransfer.query.filter_by(
                asset_id=asset.id,
                to_user_id=user_id
            ).order_by(AssetTransfer.created_at.desc()).first()
            
            user_assets.append({
                'asset': asset.to_dict(),
                'transfer_date': latest_transfer.created_at.isoformat() if latest_transfer else None,
                'transfer_reason': latest_transfer.reason if latest_transfer else None
            })
        
        return user_assets
    
    @staticmethod
    def get_transfer_statistics(grant_id: int) -> Dict:
        """Get transfer statistics for a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        stats = {
            'total_assets': len(assets),
            'assets_with_custodians': 0,
            'unassigned_assets': 0,
            'total_transfers': 0,
            'pending_transfers': 0,
            'most_transferred_asset': None,
            'transfer_frequency': {}
        }
        
        transfer_counts = {}
        
        for asset in assets:
            if asset.custodian_user_id:
                stats['assets_with_custodians'] += 1
            else:
                stats['unassigned_assets'] += 1
            
            # Count transfers for this asset
            asset_transfers = AssetTransfer.query.filter_by(asset_id=asset.id).count()
            stats['total_transfers'] += asset_transfers
            transfer_counts[asset.id] = asset_transfers
        
        # Count pending transfers
        pending_transfers = AssetTransfer.query.join(Asset).filter(
            Asset.grant_id == grant_id,
            AssetTransfer.approved_by.is_(None)
        ).count()
        stats['pending_transfers'] = pending_transfers
        
        # Find most transferred asset
        if transfer_counts:
            most_transferred_asset_id = max(transfer_counts, key=transfer_counts.get)
            most_transferred_asset = Asset.query.get(most_transferred_asset_id)
            if most_transferred_asset:
                stats['most_transferred_asset'] = {
                    'name': most_transferred_asset.name,
                    'transfers': transfer_counts[most_transferred_asset_id]
                }
        
        return stats
    
    @staticmethod
    def _requires_approval(asset: Asset, from_user_id: int, to_user_id: int) -> bool:
        """Check if transfer requires approval"""
        # High-value assets require approval
        if asset.purchase_cost > 5000:
            return True
        
        # Cross-grant transfers require approval
        if from_user_id:
            from_user = User.query.get(from_user_id)
            # This would need to be implemented based on your user-grant relationship
            # For now, we'll assume all transfers between different users require approval
        
        # University-owned assets require approval
        if asset.source_type == 'UNIVERSITY_OWNED':
            return True
        
        return False
    
    @staticmethod
    def _get_approvers(asset: Asset) -> List[User]:
        """Get users who can approve transfers for this asset"""
        approvers = []
        
        # Grant PI can approve
        grant = Grant.query.get(asset.grant_id)
        if grant and grant.pi_id:
            approvers.append(User.query.get(grant.pi_id))
        
        # RSU users can approve high-value transfers
        if asset.purchase_cost > 5000:
            rsu_users = User.query.filter_by(role='RSU').all()
            approvers.extend(rsu_users)
        
        # Remove duplicates
        approvers = list({user.id: user for user in approvers}.values())
        
        return approvers
    
    @staticmethod
    def validate_transfer_request(asset_id: int, from_user_id: int, to_user_id: int) -> Dict:
        """Validate transfer request before submission"""
        asset = Asset.query.get(asset_id)
        if not asset:
            return {'valid': False, 'error': 'Asset not found'}
        
        # Check asset status
        if asset.status not in ['ACTIVE', 'IN_REPAIR']:
            return {'valid': False, 'error': f'Asset with status "{asset.status}" cannot be transferred'}
        
        # Check target user
        to_user = User.query.get(to_user_id)
        if not to_user:
            return {'valid': False, 'error': 'Target user not found'}
        
        # Check current custodian
        if from_user_id and asset.custodian_user_id != from_user_id:
            return {'valid': False, 'error': 'Asset is not currently assigned to the specified user'}
        
        # Check if transfer is already pending
        existing_pending = AssetTransfer.query.filter_by(
            asset_id=asset_id,
            to_user_id=to_user_id,
            approved_by=None
        ).first()
        
        if existing_pending:
            return {'valid': False, 'error': 'Transfer to this user is already pending approval'}
        
        # Check approval requirements
        requires_approval = AssetTransferService._requires_approval(asset, from_user_id, to_user_id)
        
        return {
            'valid': True,
            'requires_approval': requires_approval,
            'asset': asset.to_dict(),
            'to_user': to_user.to_dict()
        }
