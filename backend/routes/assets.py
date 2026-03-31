"""
Asset Routes - Equipment & Asset Management API endpoints
"""

from flask import Blueprint, request, jsonify, session
from middleware.auth import token_required
from services.asset_service import AssetService
from services.asset_maintenance_service import AssetMaintenanceService
from services.asset_rules_service import AssetRulesService
from services.asset_transfer_service import AssetTransferService
from services.asset_alert_service import AssetAlertService
from services.asset_disposition_service import AssetDispositionService
from models import Asset, AssetMaintenance, AssetTransfer, User

assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/assets/request', methods=['POST'])
@token_required
def request_asset(user):
    """Request new asset from task"""
    data = request.get_json()
    
    try:
        asset, rule_result = AssetService.create_asset_request(
            data['task_id'], data, user.id
        )
        
        # Handle rule outcomes
        if rule_result['outcome'] == 'BLOCK':
            return jsonify({
                'error': 'Asset request blocked',
                'reasons': rule_result['block_reasons']
            }), 403
        elif rule_result['outcome'] == 'PRIOR_APPROVAL':
            return jsonify({
                'message': 'Asset request requires prior approval',
                'asset': asset.to_dict(),
                'approvals_needed': rule_result['prior_approval_reasons']
            }), 202
        
        return jsonify({
            'message': 'Asset request created successfully',
            'asset': asset.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create asset request'}), 500

@assets_bp.route('/assets/grant/<int:grant_id>', methods=['GET'])
@token_required
def get_grant_assets(user, grant_id):
    """Get all assets for a grant"""
    try:
        status_filter = request.args.get('status')
        assets = AssetService.get_grant_assets(grant_id, status_filter)
        
        return jsonify({
            'assets': [asset.to_dict() for asset in assets],
            'total': len(assets)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch assets'}), 500

@assets_bp.route('/assets/<int:asset_id>', methods=['GET'])
@token_required
def get_asset_details(user, asset_id):
    """Get detailed asset information"""
    try:
        asset = AssetService.get_asset_details(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        # Include maintenance and transfer records
        asset_dict = asset.to_dict()
        asset_dict['maintenance_records'] = [m.to_dict() for m in asset.maintenance_records]
        asset_dict['transfer_records'] = [t.to_dict() for t in asset.transfer_records]
        
        return jsonify(asset_dict), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch asset details'}), 500

@assets_bp.route('/assets/<int:asset_id>/status', methods=['PUT'])
@token_required
def update_asset_status(user, asset_id):
    """Update asset status"""
    data = request.get_json()
    
    try:
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        asset = AssetService.update_asset_status(
            asset_id, data['status'], user.id, data.get('notes')
        )
        
        return jsonify({
            'message': 'Asset status updated successfully',
            'asset': asset.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update asset status'}), 500

@assets_bp.route('/assets/<int:asset_id>/transfer', methods=['POST'])
@token_required
def transfer_asset(user, asset_id):
    """Transfer asset custody"""
    data = request.get_json()
    
    try:
        if not data.get('to_user_id'):
            return jsonify({'error': 'Target user is required'}), 400
        
        transfer = AssetService.transfer_asset(
            asset_id, 
            data.get('from_user_id', user.id),
            data['to_user_id'],
            data.get('reason', ''),
            user.id
        )
        
        return jsonify({
            'message': 'Asset transferred successfully',
            'transfer': transfer.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to transfer asset'}), 500

@assets_bp.route('/assets/statistics/grant/<int:grant_id>', methods=['GET'])
@token_required
def get_grant_asset_statistics(user, grant_id):
    """Get asset statistics for a grant"""
    try:
        stats = AssetService.get_asset_statistics(grant_id)
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch asset statistics'}), 500

@assets_bp.route('/assets/overdue-returns', methods=['GET'])
@token_required
def get_overdue_returns(user):
    """Get assets with overdue return dates"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        assets = AssetService.get_overdue_returns(grant_id)
        
        return jsonify({
            'assets': [asset.to_dict() for asset in assets],
            'total': len(assets)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch overdue returns'}), 500

@assets_bp.route('/assets/closeout-check/<int:grant_id>', methods=['GET'])
@token_required
def check_closeout_compliance(user, grant_id):
    """Check asset compliance for grant closeout"""
    try:
        compliance = AssetService.check_closeout_compliance(grant_id)
        return jsonify(compliance), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to check closeout compliance'}), 500

# Additional utility endpoints

@assets_bp.route('/assets/categories', methods=['GET'])
@token_required
def get_asset_categories(user):
    """Get available asset categories"""
    categories = [
        'Equipment',
        'Vehicle',
        'IT Equipment',
        'Lab Equipment',
        'Office Equipment',
        'Furniture',
        'Tools',
        'Other'
    ]
    
    return jsonify({'categories': categories}), 200

@assets_bp.route('/assets/source-types', methods=['GET'])
@token_required
def get_source_types(user):
    """Get available asset source types"""
    source_types = [
        {'value': 'PURCHASED', 'label': 'Purchase New'},
        {'value': 'LENDED', 'label': 'Lend/Rent External'},
        {'value': 'UNIVERSITY_OWNED', 'label': 'Use University Asset'}
    ]
    
    return jsonify({'source_types': source_types}), 200

@assets_bp.route('/assets/status-options', methods=['GET'])
@token_required
def get_status_options(user):
    """Get available asset status options"""
    statuses = [
        {'value': 'ACTIVE', 'label': 'Active', 'color': 'green'},
        {'value': 'IN_REPAIR', 'label': 'In Repair', 'color': 'yellow'},
        {'value': 'LENDED', 'label': 'Lended', 'color': 'blue'},
        {'value': 'RETURNED', 'label': 'Returned', 'color': 'gray'},
        {'value': 'TRANSFERRED', 'label': 'Transferred', 'color': 'purple'},
        {'value': 'DISPOSED', 'label': 'Disposed', 'color': 'red'},
        {'value': 'LOST', 'label': 'Lost', 'color': 'red'}
    ]
    
    return jsonify({'statuses': statuses}), 200

# Maintenance endpoints
@assets_bp.route('/assets/<int:asset_id>/maintenance', methods=['POST'])
@token_required
def create_maintenance_record(user, asset_id):
    """Create maintenance record for an asset"""
    data = request.get_json()
    
    try:
        maintenance = AssetMaintenanceService.create_maintenance_record(
            asset_id, data, user.id
        )
        
        return jsonify({
            'message': 'Maintenance record created',
            'maintenance': maintenance.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create maintenance record'}), 500

@assets_bp.route('/assets/<int:asset_id>/maintenance/history', methods=['GET'])
@token_required
def get_maintenance_history(user, asset_id):
    """Get maintenance history for an asset"""
    try:
        history = AssetMaintenanceService.get_maintenance_history(asset_id)
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch maintenance history'}), 500

@assets_bp.route('/assets/maintenance/upcoming/<int:grant_id>', methods=['GET'])
@token_required
def get_upcoming_maintenance(user, grant_id):
    """Get assets with upcoming maintenance"""
    try:
        days_ahead = request.args.get('days', 30, type=int)
        upcoming = AssetMaintenanceService.get_upcoming_maintenance(grant_id, days_ahead)
        
        return jsonify({
            'upcoming_maintenance': upcoming,
            'total': len(upcoming)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch upcoming maintenance'}), 500

@assets_bp.route('/assets/maintenance/overdue/<int:grant_id>', methods=['GET'])
@token_required
def get_overdue_maintenance(user, grant_id):
    """Get assets with overdue maintenance"""
    try:
        overdue = AssetMaintenanceService.get_overdue_maintenance(grant_id)
        
        return jsonify({
            'overdue_maintenance': overdue,
            'total': len(overdue)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch overdue maintenance'}), 500

@assets_bp.route('/assets/maintenance/statistics/<int:grant_id>', methods=['GET'])
@token_required
def get_maintenance_statistics(user, grant_id):
    """Get maintenance statistics for a grant"""
    try:
        stats = AssetMaintenanceService.get_maintenance_statistics(grant_id)
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch maintenance statistics'}), 500

@assets_bp.route('/assets/<int:asset_id>/maintenance/recommendations', methods=['GET'])
@token_required
def get_maintenance_recommendations(user, asset_id):
    """Get maintenance recommendations for an asset"""
    try:
        recommendations = AssetMaintenanceService.get_maintenance_recommendations(asset_id)
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch maintenance recommendations'}), 500

@assets_bp.route('/assets/maintenance/<int:maintenance_id>/complete', methods=['PUT'])
@token_required
def complete_maintenance(user, maintenance_id):
    """Complete a scheduled maintenance"""
    data = request.get_json()
    
    try:
        maintenance = AssetMaintenanceService.complete_maintenance(maintenance_id, data, user.id)
        
        return jsonify({
            'message': 'Maintenance completed successfully',
            'maintenance': maintenance.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to complete maintenance'}), 500

# Compliance endpoints
@assets_bp.route('/assets/<int:asset_id>/compliance', methods=['GET'])
@token_required
def get_asset_compliance(user, asset_id):
    """Get compliance status for a specific asset"""
    try:
        compliance = AssetService.get_asset_compliance(asset_id)
        return jsonify(compliance), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch asset compliance'}), 500

@assets_bp.route('/assets/compliance/alerts', methods=['GET'])
@token_required
def get_compliance_alerts(user):
    """Get compliance alerts for assets"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        alerts = AssetService.get_compliance_alerts(grant_id)
        
        return jsonify({
            'alerts': alerts,
            'total': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch compliance alerts'}), 500

@assets_bp.route('/assets/compliance/report/<int:grant_id>', methods=['GET'])
@token_required
def get_compliance_report(user, grant_id):
    """Generate comprehensive compliance report for a grant"""
    try:
        report = AssetService.generate_compliance_report(grant_id)
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate compliance report'}), 500

@assets_bp.route('/assets/<int:asset_id>/recommendations', methods=['GET'])
@token_required
def get_asset_recommendations(user, asset_id):
    """Get recommendations for asset management"""
    try:
        recommendations = AssetService.get_asset_recommendations(asset_id)
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch asset recommendations'}), 500

# Rules validation endpoint
@assets_bp.route('/assets/validate-request', methods=['POST'])
@token_required
def validate_asset_request(user):
    """Validate asset request against rules without creating asset"""
    data = request.get_json()
    
    try:
        rule_result = AssetRulesService.evaluate_asset_request(data, data['grant_id'], user.id)
        return jsonify(rule_result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to validate request'}), 500

# Transfer endpoints
@assets_bp.route('/assets/transfer/request', methods=['POST'])
@token_required
def request_asset_transfer(user):
    """Request asset transfer"""
    data = request.get_json()
    
    try:
        # Validate transfer first
        validation = AssetTransferService.validate_transfer_request(
            data['asset_id'], data.get('from_user_id'), data['to_user_id']
        )
        
        if not validation['valid']:
            return jsonify({'error': validation['error']}), 400
        
        # Create transfer request
        transfer = AssetTransferService.request_transfer_approval(
            data['asset_id'],
            data.get('from_user_id'),
            data['to_user_id'],
            data['reason'],
            user.id
        )
        
        return jsonify({
            'message': 'Transfer request submitted',
            'transfer': transfer.to_dict(),
            'requires_approval': validation['requires_approval']
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to request transfer'}), 500

@assets_bp.route('/assets/transfer/initiate', methods=['POST'])
@token_required
def initiate_asset_transfer(user):
    """Initiate direct asset transfer (no approval required)"""
    data = request.get_json()
    
    try:
        transfer = AssetTransferService.initiate_transfer(
            data['asset_id'],
            data.get('from_user_id'),
            data['to_user_id'],
            data['reason'],
            user.id
        )
        
        return jsonify({
            'message': 'Asset transferred successfully',
            'transfer': transfer.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to transfer asset'}), 500

@assets_bp.route('/assets/transfer/<int:transfer_id>/approve', methods=['POST'])
@token_required
def approve_asset_transfer(user, transfer_id):
    """Approve a pending asset transfer"""
    data = request.get_json()
    
    try:
        transfer = AssetTransferService.approve_transfer(transfer_id, user.id, data.get('notes'))
        
        return jsonify({
            'message': 'Transfer approved successfully',
            'transfer': transfer.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to approve transfer'}), 500

@assets_bp.route('/assets/transfer/<int:transfer_id>/reject', methods=['POST'])
@token_required
def reject_asset_transfer(user, transfer_id):
    """Reject a pending asset transfer"""
    data = request.get_json()
    
    try:
        transfer = AssetTransferService.reject_transfer(transfer_id, user.id, data['rejection_reason'])
        
        return jsonify({
            'message': 'Transfer rejected',
            'transfer': transfer.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to reject transfer'}), 500

@assets_bp.route('/assets/transfers/pending', methods=['GET'])
@token_required
def get_pending_transfers(user):
    """Get pending transfer requests"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        pending = AssetTransferService.get_pending_transfers(grant_id, user_id)
        
        return jsonify({
            'pending_transfers': pending,
            'total': len(pending)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch pending transfers'}), 500

@assets_bp.route('/assets/transfers/history', methods=['GET'])
@token_required
def get_transfer_history(user):
    """Get transfer history"""
    try:
        asset_id = request.args.get('asset_id', type=int)
        grant_id = request.args.get('grant_id', type=int)
        
        history = AssetTransferService.get_transfer_history(asset_id, grant_id)
        
        return jsonify({
            'transfer_history': history,
            'total': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transfer history'}), 500

@assets_bp.route('/assets/transfers/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_assets(user, user_id):
    """Get assets currently assigned to a user"""
    try:
        user_assets = AssetTransferService.get_user_assets(user_id)
        
        return jsonify({
            'user_assets': user_assets,
            'total': len(user_assets)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch user assets'}), 500

@assets_bp.route('/assets/transfers/statistics/<int:grant_id>', methods=['GET'])
@token_required
def get_transfer_statistics(user, grant_id):
    """Get transfer statistics for a grant"""
    try:
        stats = AssetTransferService.get_transfer_statistics(grant_id)
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transfer statistics'}), 500

@assets_bp.route('/assets/transfer/validate', methods=['POST'])
@token_required
def validate_transfer_request(user):
    """Validate transfer request before submission"""
    data = request.get_json()
    
    try:
        validation = AssetTransferService.validate_transfer_request(
            data['asset_id'], data.get('from_user_id'), data['to_user_id']
        )
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to validate transfer'}), 500

# Alert endpoints
@assets_bp.route('/assets/alerts', methods=['GET'])
@token_required
def get_asset_alerts(user):
    """Get all asset alerts"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        alerts = AssetAlertService.generate_all_alerts(grant_id)
        
        return jsonify({
            'alerts': alerts,
            'total': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch alerts'}), 500

@assets_bp.route('/assets/alerts/summary', methods=['GET'])
@token_required
def get_alert_summary(user):
    """Get alert summary by category and severity"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        summary = AssetAlertService.get_alert_summary(grant_id)
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch alert summary'}), 500

@assets_bp.route('/assets/alerts/trends/<int:grant_id>', methods=['GET'])
@token_required
def get_alert_trends(user, grant_id):
    """Get alert trends over time"""
    try:
        days = request.args.get('days', 30, type=int)
        trends = AssetAlertService.get_alert_trends(grant_id, days)
        return jsonify(trends), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch alert trends'}), 500

@assets_bp.route('/assets/alerts/<alert_id>/dismiss', methods=['POST'])
@token_required
def dismiss_alert(user, alert_id):
    """Dismiss an alert"""
    data = request.get_json()
    
    try:
        success = AssetAlertService.dismiss_alert(alert_id, user.id, data.get('reason'))
        
        if success:
            return jsonify({'message': 'Alert dismissed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to dismiss alert'}), 400
        
    except Exception as e:
        return jsonify({'error': 'Failed to dismiss alert'}), 500

@assets_bp.route('/assets/alerts/check', methods=['POST'])
@token_required
def schedule_alert_check(user):
    """Schedule alert check (for testing/manual triggering)"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        result = AssetAlertService.schedule_alert_check(grant_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to schedule alert check'}), 500

# Disposition endpoints
@assets_bp.route('/assets/<int:asset_id>/disposition-options', methods=['GET'])
@token_required
def get_disposition_options(user, asset_id):
    """Get available disposition options for an asset"""
    try:
        options = AssetDispositionService.get_disposition_options(asset_id)
        return jsonify({'options': options}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch disposition options'}), 500

@assets_bp.route('/assets/disposition/validate', methods=['POST'])
@token_required
def validate_disposition(user):
    """Validate disposition method for an asset"""
    data = request.get_json()
    
    try:
        validation = AssetDispositionService.validate_disposition(
            data['asset_id'], 
            data['disposition_method']
        )
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to validate disposition'}), 500

@assets_bp.route('/assets/<int:asset_id>/dispose', methods=['POST'])
@token_required
def dispose_asset(user, asset_id):
    """Dispose an asset"""
    data = request.get_json()
    
    try:
        asset = AssetDispositionService.dispose_asset(asset_id, data, user.id)
        
        return jsonify({
            'message': 'Asset disposed successfully',
            'asset': asset.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to dispose asset'}), 500

@assets_bp.route('/assets/<int:asset_id>/transfer-university', methods=['POST'])
@token_required
def transfer_to_university(user, asset_id):
    """Transfer asset to university ownership"""
    data = request.get_json()
    
    try:
        asset = AssetDispositionService.transfer_to_university(asset_id, data, user.id)
        
        return jsonify({
            'message': 'Asset transferred to university successfully',
            'asset': asset.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to transfer asset'}), 500

@assets_bp.route('/assets/<int:asset_id>/return-lender', methods=['POST'])
@token_required
def return_to_lender(user, asset_id):
    """Return lended asset to lender"""
    data = request.get_json()
    
    try:
        asset = AssetDispositionService.return_to_lender(asset_id, data, user.id)
        
        return jsonify({
            'message': 'Asset returned to lender successfully',
            'asset': asset.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to return asset'}), 500

@assets_bp.route('/assets/disposition/pending', methods=['GET'])
@token_required
def get_pending_dispositions(user):
    """Get assets pending disposition"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        pending = AssetDispositionService.get_pending_dispositions(grant_id)
        
        return jsonify({
            'pending_dispositions': pending,
            'total': len(pending)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch pending dispositions'}), 500

@assets_bp.route('/assets/disposition/summary/<int:grant_id>', methods=['GET'])
@token_required
def get_disposition_summary(user, grant_id):
    """Get disposition summary for a grant"""
    try:
        summary = AssetDispositionService.get_disposition_summary(grant_id)
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch disposition summary'}), 500

@assets_bp.route('/assets/disposition/report/<int:grant_id>', methods=['GET'])
@token_required
def get_disposition_report(user, grant_id):
    """Generate comprehensive disposition report for a grant"""
    try:
        report = AssetDispositionService.generate_disposition_report(grant_id)
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate disposition report'}), 500

@assets_bp.route('/assets/closeout-readiness/<int:grant_id>', methods=['GET'])
@token_required
def check_closeout_readiness(user, grant_id):
    """Check if grant is ready for closeout based on asset disposition"""
    try:
        readiness = AssetDispositionService.check_closeout_readiness(grant_id)
        return jsonify(readiness), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to check closeout readiness'}), 500
