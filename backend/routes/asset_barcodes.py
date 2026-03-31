"""
Asset Barcode/QR Code Routes - Barcode and QR code management endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from middleware.auth import token_required
from services.asset_barcode_service import AssetBarcodeService
from models import Asset
import os

barcodes_bp = Blueprint('asset_barcodes', __name__)

@barcodes_bp.route('/assets/<int:asset_id>/barcode', methods=['POST'])
@token_required
def generate_asset_barcode(user, asset_id):
    """Generate barcode for an asset"""
    try:
        barcode_type = request.json.get('barcode_type', 'code128')
        barcode_info = AssetBarcodeService.generate_asset_barcode(asset_id, barcode_type)
        
        return jsonify({
            'message': 'Barcode generated successfully',
            'barcode_info': barcode_info
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate barcode'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/qrcode', methods=['POST'])
@token_required
def generate_asset_qrcode(user, asset_id):
    """Generate QR code for an asset"""
    try:
        include_details = request.json.get('include_details', True)
        qr_info = AssetBarcodeService.generate_asset_qrcode(asset_id, include_details)
        
        return jsonify({
            'message': 'QR code generated successfully',
            'qr_info': qr_info
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate QR code'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/label', methods=['POST'])
@token_required
def generate_asset_label(user, asset_id):
    """Generate comprehensive asset label"""
    try:
        label_format = request.json.get('label_format', 'standard')
        label_info = AssetBarcodeService.generate_asset_label(asset_id, label_format)
        
        return jsonify({
            'message': 'Asset label generated successfully',
            'label_info': label_info
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate asset label'}), 500

@barcodes_bp.route('/assets/scan', methods=['POST'])
@token_required
def scan_asset_barcode(user):
    """Process barcode/QR code scan"""
    try:
        data = request.get_json()
        barcode_data = data.get('barcode_data')
        
        if not barcode_data:
            return jsonify({'error': 'Barcode data is required'}), 400
        
        scan_result = AssetBarcodeService.scan_asset_barcode(barcode_data, user.id)
        
        if 'error' in scan_result:
            return jsonify(scan_result), 400
        
        return jsonify(scan_result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to process scan'}), 500

@barcodes_bp.route('/assets/lookup', methods=['POST'])
@token_required
def lookup_asset_by_barcode(user):
    """Look up asset by barcode/QR code data"""
    try:
        data = request.get_json()
        barcode_data = data.get('barcode_data')
        
        if not barcode_data:
            return jsonify({'error': 'Barcode data is required'}), 400
        
        lookup_result = AssetBarcodeService.get_asset_by_barcode(barcode_data)
        
        if 'error' in lookup_result:
            return jsonify(lookup_result), 404
        
        return jsonify(lookup_result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to lookup asset'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/barcode', methods=['GET'])
@token_required
def get_asset_barcode(user, asset_id):
    """Get existing barcode for an asset"""
    try:
        barcode_info = AssetBarcodeService.get_asset_barcode(asset_id)
        
        if 'error' in barcode_info:
            return jsonify(barcode_info), 404
        
        return jsonify(barcode_info), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch barcode'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/qrcode', methods=['GET'])
@token_required
def get_asset_qrcode(user, asset_id):
    """Get existing QR code for an asset"""
    try:
        qr_info = AssetBarcodeService.get_asset_qrcode(asset_id)
        
        if 'error' in qr_info:
            return jsonify(qr_info), 404
        
        return jsonify(qr_info), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch QR code'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/barcode/download', methods=['GET'])
@token_required
def download_asset_barcode(user, asset_id):
    """Download barcode image"""
    try:
        barcode_info = AssetBarcodeService.get_asset_barcode(asset_id)
        
        if 'error' in barcode_info:
            return jsonify(barcode_info), 404
        
        barcode_path = barcode_info['barcode_path']
        
        if not os.path.exists(barcode_path):
            return jsonify({'error': 'Barcode file not found'}), 404
        
        return send_file(
            barcode_path,
            as_attachment=True,
            download_name=barcode_info['barcode_filename'],
            mimetype='image/png'
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to download barcode'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/qrcode/download', methods=['GET'])
@token_required
def download_asset_qrcode(user, asset_id):
    """Download QR code image"""
    try:
        qr_info = AssetBarcodeService.get_asset_qrcode(asset_id)
        
        if 'error' in qr_info:
            return jsonify(qr_info), 404
        
        qr_path = qr_info['qr_path']
        
        if not os.path.exists(qr_path):
            return jsonify({'error': 'QR code file not found'}), 404
        
        return send_file(
            qr_path,
            as_attachment=True,
            download_name=qr_info['qr_filename'],
            mimetype='image/png'
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to download QR code'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/label/download', methods=['GET'])
@token_required
def download_asset_label(user, asset_id):
    """Download asset label"""
    try:
        label_format = request.args.get('format', 'standard')
        label_info = AssetBarcodeService.generate_asset_label(asset_id, label_format)
        
        label_path = label_info['label_path']
        
        if not os.path.exists(label_path):
            return jsonify({'error': 'Label file not found'}), 404
        
        return send_file(
            label_path,
            as_attachment=True,
            download_name=label_info['label_filename'],
            mimetype='image/png'
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to download label'}), 500

@barcodes_bp.route('/assets/grant/<int:grant_id>/barcodes/batch', methods=['POST'])
@token_required
def generate_batch_barcodes(user, grant_id):
    """Generate barcodes for all assets in a grant"""
    try:
        barcode_type = request.json.get('barcode_type', 'code128')
        batch_results = AssetBarcodeService.generate_batch_barcodes(grant_id, barcode_type)
        
        return jsonify({
            'message': f'Batch barcode generation completed',
            'results': batch_results,
            'total': len(batch_results),
            'successful': len([r for r in batch_results if r['status'] == 'success']),
            'failed': len([r for r in batch_results if r['status'] == 'error'])
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate batch barcodes'}), 500

@barcodes_bp.route('/assets/grant/<int:grant_id>/qrcodes/batch', methods=['POST'])
@token_required
def generate_batch_qrcodes(user, grant_id):
    """Generate QR codes for all assets in a grant"""
    try:
        include_details = request.json.get('include_details', True)
        batch_results = AssetBarcodeService.generate_batch_qrcodes(grant_id, include_details)
        
        return jsonify({
            'message': f'Batch QR code generation completed',
            'results': batch_results,
            'total': len(batch_results),
            'successful': len([r for r in batch_results if r['status'] == 'success']),
            'failed': len([r for r in batch_results if r['status'] == 'error'])
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate batch QR codes'}), 500

@barcodes_bp.route('/assets/grant/<int:grant_id>/labels/batch', methods=['POST'])
@token_required
def generate_batch_labels(user, grant_id):
    """Generate labels for all assets in a grant"""
    try:
        label_format = request.json.get('label_format', 'standard')
        
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        batch_results = []
        
        for asset in assets:
            try:
                label_info = AssetBarcodeService.generate_asset_label(asset.id, label_format)
                batch_results.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'label_info': label_info,
                    'status': 'success'
                })
            except Exception as e:
                batch_results.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'error': str(e),
                    'status': 'error'
                })
        
        return jsonify({
            'message': f'Batch label generation completed',
            'results': batch_results,
            'total': len(batch_results),
            'successful': len([r for r in batch_results if r['status'] == 'success']),
            'failed': len([r for r in batch_results if r['status'] == 'error'])
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate batch labels'}), 500

@barcodes_bp.route('/assets/barcodes/scan-statistics', methods=['GET'])
@token_required
def get_scan_statistics(user):
    """Get scanning statistics"""
    try:
        grant_id = request.args.get('grant_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        stats = AssetBarcodeService.get_scan_statistics(grant_id, days)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch scan statistics'}), 500

@barcodes_bp.route('/assets/barcodes/validate', methods=['POST'])
@token_required
def validate_barcode_data(user):
    """Validate barcode data format"""
    try:
        data = request.get_json()
        barcode_data = data.get('barcode_data')
        
        if not barcode_data:
            return jsonify({'error': 'Barcode data is required'}), 400
        
        validation = AssetBarcodeService.validate_barcode_data(barcode_data)
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to validate barcode data'}), 500

@barcodes_bp.route('/assets/barcodes/supported-types', methods=['GET'])
@token_required
def get_supported_barcode_types(user):
    """Get supported barcode types"""
    try:
        types = AssetBarcodeService.get_supported_barcode_types()
        return jsonify({'supported_types': types}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch supported types'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/barcode', methods=['DELETE'])
@token_required
def delete_asset_barcode(user, asset_id):
    """Delete barcode for an asset"""
    try:
        success = AssetBarcodeService.delete_asset_barcode(asset_id, user.id)
        
        if success:
            return jsonify({'message': 'Barcode deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete barcode'}), 400
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to delete barcode'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/qrcode', methods=['DELETE'])
@token_required
def delete_asset_qrcode(user, asset_id):
    """Delete QR code for an asset"""
    try:
        success = AssetBarcodeService.delete_asset_qrcode(asset_id, user.id)
        
        if success:
            return jsonify({'message': 'QR code deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete QR code'}), 400
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to delete QR code'}), 500

@barcodes_bp.route('/assets/mobile/scan', methods=['POST'])
@token_required
def mobile_scan_asset(user):
    """Mobile-optimized asset scanning endpoint"""
    try:
        data = request.get_json()
        barcode_data = data.get('barcode_data')
        location = data.get('location', {})
        notes = data.get('notes', '')
        
        if not barcode_data:
            return jsonify({'error': 'Barcode data is required'}), 400
        
        # Process scan
        scan_result = AssetBarcodeService.scan_asset_barcode(barcode_data, user.id)
        
        if 'error' in scan_result:
            return jsonify(scan_result), 400
        
        # Add mobile-specific data
        scan_result['mobile_data'] = {
            'location': location,
            'notes': notes,
            'device_info': {
                'user_agent': request.headers.get('User-Agent', ''),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        return jsonify(scan_result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to process mobile scan'}), 500

@barcodes_bp.route('/assets/<int:asset_id>/scan-history', methods=['GET'])
@token_required
def get_asset_scan_history(user, asset_id):
    """Get scan history for an asset"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        scan_history = asset.scan_history or []
        
        # Sort by scan time (newest first)
        scan_history.sort(key=lambda x: x.get('scan_time', ''), reverse=True)
        
        return jsonify({
            'scan_history': scan_history,
            'total_scans': len(scan_history),
            'last_scanned': asset.last_scanned
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch scan history'}), 500
