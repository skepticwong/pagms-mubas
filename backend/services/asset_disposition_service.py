"""
Asset Disposition Service - Asset disposition and closeout workflows
Handles asset disposal, transfer, and retirement processes
"""

from datetime import datetime
from typing import Dict, List, Optional
from models import db, Asset, User, Grant
from services.notification_service import NotificationService

class AssetDispositionService:
    """Service for managing asset disposition and closeout workflows"""
    
    @staticmethod
    def dispose_asset(asset_id: int, disposition_data: Dict, user_id: int) -> Asset:
        """Dispose an asset with proper documentation"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Validate asset can be disposed
        if asset.status not in ['ACTIVE', 'IN_REPAIR', 'LENDED']:
            raise ValueError(f"Asset with status '{asset.status}' cannot be disposed")
        
        # Update asset disposition information
        asset.status = 'DISPOSED'
        asset.disposition_method = disposition_data['method']
        asset.disposition_approved_by = user_id
        asset.disposition_date = datetime.utcnow().date()
        asset.disposition_notes = disposition_data.get('notes', '')
        asset.actual_return_date = asset.disposition_date  # Set return date for lended assets
        asset.custodian_user_id = None  # Clear custodian
        asset.updated_at = datetime.utcnow()
        
        # Store supporting documents
        if disposition_data.get('documents'):
            asset.supporting_documents = asset.supporting_documents or {}
            asset.supporting_documents['disposition'] = disposition_data['documents']
        
        # Create notifications
        grant = Grant.query.get(asset.grant_id)
        if grant and grant.pi_id:
            NotificationService.create_notification(
                user_id=grant.pi_id,
                title=f'Asset Disposed: {asset.name}',
                message=f'Asset {asset.name} has been disposed via {asset.disposition_method}',
                type='asset_disposition',
                related_id=asset.id
            )
        
        db.session.commit()
        return asset
    
    @staticmethod
    def transfer_to_university(asset_id: int, transfer_data: Dict, user_id: int) -> Asset:
        """Transfer asset to university ownership"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Update asset for university transfer
        asset.status = 'TRANSFERRED'
        asset.disposition_method = 'Transfer to University'
        asset.disposition_approved_by = user_id
        asset.disposition_date = datetime.utcnow().date()
        asset.disposition_notes = transfer_data.get('notes', f'Transferred to university inventory')
        asset.owner_name = 'MUBAS'
        asset.source_type = 'UNIVERSITY_OWNED'
        asset.custodian_user_id = None
        asset.updated_at = datetime.utcnow()
        
        # Store transfer documents
        if transfer_data.get('documents'):
            asset.supporting_documents = asset.supporting_documents or {}
            asset.supporting_documents['university_transfer'] = transfer_data['documents']
        
        # Create notifications
        grant = Grant.query.get(asset.grant_id)
        if grant and grant.pi_id:
            NotificationService.create_notification(
                user_id=grant.pi_id,
                title=f'Asset Transferred to University: {asset.name}',
                message=f'Asset {asset.name} has been transferred to university ownership',
                type='asset_disposition',
                related_id=asset.id
            )
        
        db.session.commit()
        return asset
    
    @staticmethod
    def return_to_lender(asset_id: int, return_data: Dict, user_id: int) -> Asset:
        """Return lended asset to original lender"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        if asset.source_type != 'LENDED':
            raise ValueError("Only lended assets can be returned to lender")
        
        # Update asset for return
        asset.status = 'RETURNED'
        asset.actual_return_date = datetime.utcnow().date()
        asset.custodian_user_id = None
        asset.updated_at = datetime.utcnow()
        
        # Store return documents
        if return_data.get('documents'):
            asset.supporting_documents = asset.supporting_documents or {}
            asset.supporting_documents['lender_return'] = return_data['documents']
        
        # Create notifications
        grant = Grant.query.get(asset.grant_id)
        if grant and grant.pi_id:
            NotificationService.create_notification(
                user_id=grant.pi_id,
                title=f'Asset Returned: {asset.name}',
                message=f'Asset {asset.name} has been returned to {asset.owner_name}',
                type='asset_disposition',
                related_id=asset.id
            )
        
        db.session.commit()
        return asset
    
    @staticmethod
    def get_disposition_options(asset_id: int) -> List[Dict]:
        """Get available disposition options for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        options = []
        
        # Options based on source type
        if asset.source_type == 'PURCHASED':
            options.extend([
                {
                    'value': 'Transfer to University',
                    'label': 'Transfer to University',
                    'description': 'Transfer asset to university inventory for continued use',
                    'requires_approval': asset.purchase_cost > 5000
                },
                {
                    'value': 'Sell',
                    'label': 'Sell Asset',
                    'description': 'Sell asset and return funds to grant',
                    'requires_approval': asset.purchase_cost > 1000
                },
                {
                    'value': 'Donate',
                    'label': 'Donate Asset',
                    'description': 'Donate asset to qualified organization',
                    'requires_approval': asset.purchase_cost > 1000
                },
                {
                    'value': 'Destroy',
                    'label': 'Destroy Asset',
                    'description': 'Properly dispose of asset (recycling, hazardous waste, etc.)',
                    'requires_approval': asset.purchase_cost > 500
                }
            ])
        
        elif asset.source_type == 'LENDED':
            options.extend([
                {
                    'value': 'Return to Lender',
                    'label': 'Return to Lender',
                    'description': f'Return asset to {asset.owner_name}',
                    'requires_approval': False
                }
            ])
        
        elif asset.source_type == 'UNIVERSITY_OWNED':
            options.extend([
                {
                    'value': 'Return to University',
                    'label': 'Return to University Pool',
                    'description': 'Return asset to university inventory pool',
                    'requires_approval': False
                }
            ])
        
        # Category-specific options
        if 'Vehicle' in (asset.category or ''):
            options.append({
                'value': 'Vehicle Auction',
                'label': 'Vehicle Auction',
                'description': 'Sell vehicle through university auction process',
                'requires_approval': True
            })
        
        if 'IT' in (asset.category or '') or 'Computer' in (asset.category or ''):
            options.extend([
                {
                    'value': 'IT Recycling',
                    'label': 'IT Recycling',
                    'description': 'Recycle through certified IT disposal program',
                    'requires_approval': False
                },
                {
                    'value': 'Data Sanitization & Reuse',
                    'label': 'Data Sanitization & Reuse',
                    'description': 'Sanitize data and repurpose within university',
                    'requires_approval': asset.purchase_cost > 500
                }
            ])
        
        return options
    
    @staticmethod
    def validate_disposition(asset_id: int, disposition_method: str) -> Dict:
        """Validate if disposition method is allowed for this asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            return {'valid': False, 'error': 'Asset not found'}
        
        # Check asset status
        if asset.status not in ['ACTIVE', 'IN_REPAIR', 'LENDED']:
            return {'valid': False, 'error': f'Asset with status "{asset.status}" cannot be disposed'}
        
        # Get available options
        options = AssetDispositionService.get_disposition_options(asset_id)
        valid_option = next((opt for opt in options if opt['value'] == disposition_method), None)
        
        if not valid_option:
            return {'valid': False, 'error': 'Disposition method not allowed for this asset'}
        
        # Check if approval is required
        requires_approval = valid_option['requires_approval']
        
        # Additional validation based on method
        if disposition_method == 'Return to Lender' and asset.source_type != 'LENDED':
            return {'valid': False, 'error': 'Only lended assets can be returned to lender'}
        
        if disposition_method == 'Transfer to University' and asset.purchase_cost > 25000:
            requires_approval = True  # High-value items always require approval
        
        return {
            'valid': True,
            'requires_approval': requires_approval,
            'asset': asset.to_dict(),
            'option': valid_option
        }
    
    @staticmethod
    def get_pending_dispositions(grant_id: int = None) -> List[Dict]:
        """Get assets pending disposition"""
        query = Asset.query.filter(
            Asset.status.in_(['ACTIVE', 'IN_REPAIR', 'LENDED'])
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        assets = query.all()
        pending = []
        
        for asset in assets:
            # Check if asset needs disposition (closeout approaching)
            grant = Grant.query.get(asset.grant_id)
            if grant and hasattr(grant, 'end_date'):
                days_to_close = (grant.end_date - datetime.utcnow().date()).days
                
                if days_to_close <= 90:  # Within 90 days of closeout
                    pending.append({
                        'asset': asset.to_dict(),
                        'days_to_closeout': days_to_close,
                        'urgency': 'high' if days_to_close <= 30 else 'medium',
                        'disposition_options': AssetDispositionService.get_disposition_options(asset.id)
                    })
        
        # Sort by urgency and days to closeout
        pending.sort(key=lambda x: (x['days_to_closeout'], x['urgency']))
        
        return pending
    
    @staticmethod
    def get_disposition_summary(grant_id: int) -> Dict:
        """Get disposition summary for a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        summary = {
            'total_assets': len(assets),
            'disposed': 0,
            'transferred': 0,
            'returned': 0,
            'pending_disposition': 0,
            'total_value_disposed': 0,
            'disposition_methods': {},
            'high_value_pending': []
        }
        
        for asset in assets:
            if asset.status == 'DISPOSED':
                summary['disposed'] += 1
                summary['total_value_disposed'] += asset.purchase_cost or 0
                
                if asset.disposition_method:
                    method = asset.disposition_method
                    if method not in summary['disposition_methods']:
                        summary['disposition_methods'][method] = 0
                    summary['disposition_methods'][method] += 1
            
            elif asset.status == 'TRANSFERRED':
                summary['transferred'] += 1
                summary['total_value_disposed'] += asset.purchase_cost or 0
            
            elif asset.status == 'RETURNED':
                summary['returned'] += 1
            
            elif asset.status in ['ACTIVE', 'IN_REPAIR', 'LENDED']:
                summary['pending_disposition'] += 1
                
                # Track high-value assets pending disposition
                if asset.purchase_cost and asset.purchase_cost > 5000:
                    summary['high_value_pending'].append({
                        'name': asset.name,
                        'value': asset.purchase_cost,
                        'status': asset.status
                    })
        
        return summary
    
    @staticmethod
    def generate_disposition_report(grant_id: int) -> Dict:
        """Generate comprehensive disposition report for a grant"""
        summary = AssetDispositionService.get_disposition_summary(grant_id)
        pending = AssetDispositionService.get_pending_dispositions(grant_id)
        
        report = {
            'grant_id': grant_id,
            'summary': summary,
            'pending_dispositions': pending,
            'recommendations': [],
            'compliance_status': 'compliant'
        }
        
        # Add recommendations
        if summary['pending_disposition'] > 0:
            report['recommendations'].append(f"{summary['pending_disposition']} assets require disposition")
            report['compliance_status'] = 'non_compliant'
        
        if summary['high_value_pending']:
            report['recommendations'].append(f"{len(summary['high_value_pending'])} high-value assets pending disposition")
        
        if pending:
            urgent_count = len([p for p in pending if p['urgency'] == 'high'])
            if urgent_count > 0:
                report['recommendations'].append(f"{urgent_count} assets require immediate attention")
        
        # Add method-specific recommendations
        if summary['disposition_methods']:
            most_common = max(summary['disposition_methods'], key=summary['disposition_methods'].get)
            report['recommendations'].append(f"Most common disposition method: {most_common}")
        
        return report
    
    @staticmethod
    def check_closeout_readiness(grant_id: int) -> Dict:
        """Check if grant is ready for closeout based on asset disposition"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        active_assets = [a for a in assets if a.status in ['ACTIVE', 'IN_REPAIR', 'LENDED']]
        
        if not active_assets:
            return {
                'ready': True,
                'message': 'All assets properly disposed',
                'remaining_assets': 0
            }
        
        # Categorize remaining assets
        high_value = [a for a in active_assets if a.purchase_cost and a.purchase_cost > 5000]
        lended_overdue = [a for a in active_assets if a.source_type == 'LENDED' and a.expected_return_date and a.expected_return_date < datetime.utcnow().date()]
        
        readiness = {
            'ready': False,
            'message': f'{len(active_assets)} assets require disposition before closeout',
            'remaining_assets': len(active_assets),
            'high_value_count': len(high_value),
            'overdue_returns': len(lended_overdue),
            'blocks_closeout': len(high_value) > 0 or len(lended_overdue) > 0
        }
        
        if readiness['blocks_closeout']:
            readiness['message'] += ' (High-value or overdue items block closeout)'
        
        return readiness
