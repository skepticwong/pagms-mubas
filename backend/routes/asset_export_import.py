"""
Asset Export/Import Routes - Data export and import endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from middleware.auth import token_required
from werkzeug.datastructures import FileStorage
from services.asset_export_service import AssetExportService
from models import Asset, Grant
import io

export_import_bp = Blueprint('asset_export_import', __name__)

# Export endpoints
@export_import_bp.route('/assets/export/<int:grant_id>/csv', methods=['GET'])
@token_required
def export_assets_csv(user, grant_id):
    """Export assets to CSV format"""
    try:
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        export_data = AssetExportService.export_assets_to_csv(grant_id, include_details)
        
        return send_file(
            io.BytesIO(export_data['content'].encode()),
            as_attachment=True,
            download_name=export_data['filename'],
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to export assets to CSV'}), 500

@export_import_bp.route('/assets/export/<int:grant_id>/json', methods=['GET'])
@token_required
def export_assets_json(user, grant_id):
    """Export assets to JSON format"""
    try:
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        export_data = AssetExportService.export_assets_to_json(grant_id, include_details)
        
        return send_file(
            io.BytesIO(export_data['content'].encode()),
            as_attachment=True,
            download_name=export_data['filename'],
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to export assets to JSON'}), 500

@export_import_bp.route('/assets/export/<int:grant_id>/excel', methods=['GET'])
@token_required
def export_assets_excel(user, grant_id):
    """Export assets to Excel format"""
    try:
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        export_data = AssetExportService.export_assets_to_excel(grant_id, include_details)
        
        return send_file(
            io.BytesIO(export_data['content'].encode()),
            as_attachment=True,
            download_name=export_data['filename'],
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to export assets to Excel'}), 500

@export_import_bp.route('/assets/export/<int:grant_id>/analytics', methods=['GET'])
@token_required
def export_analytics_csv(user, grant_id):
    """Export analytics data to CSV format"""
    try:
        export_data = AssetExportService.export_analytics_to_csv(grant_id)
        
        return send_file(
            io.BytesIO(export_data['content'].encode()),
            as_attachment=True,
            download_name=export_data['filename'],
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to export analytics'}), 500

# Import endpoints
@export_import_bp.route('/assets/import/<int:grant_id>/csv', methods=['POST'])
@token_required
def import_assets_csv(user, grant_id):
    """Import assets from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        update_existing = request.form.get('update_existing', 'false').lower() == 'true'
        
        results = AssetExportService.import_assets_from_csv(file, grant_id, user.id, update_existing)
        
        return jsonify({
            'message': 'CSV import completed',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to import CSV file'}), 500

@export_import_bp.route('/assets/import/<int:grant_id>/json', methods=['POST'])
@token_required
def import_assets_json(user, grant_id):
    """Import assets from JSON file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        update_existing = request.form.get('update_existing', 'false').lower() == 'true'
        
        results = AssetExportService.import_assets_from_json(file, grant_id, user.id, update_existing)
        
        return jsonify({
            'message': 'JSON import completed',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to import JSON file'}), 500

# Template endpoints
@export_import_bp.route('/assets/import/template/csv', methods=['GET'])
@token_required
def download_csv_template(user):
    """Download CSV import template"""
    try:
        template_data = AssetExportService.export_template('csv')
        
        return send_file(
            io.BytesIO(template_data['content'].encode()),
            as_attachment=True,
            download_name=template_data['filename'],
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate CSV template'}), 500

@export_import_bp.route('/assets/import/template/json', methods=['GET'])
@token_required
def download_json_template(user):
    """Download JSON import template"""
    try:
        template_data = AssetExportService.export_template('json')
        
        return send_file(
            io.BytesIO(template_data['content'].encode()),
            as_attachment=True,
            download_name=template_data['filename'],
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate JSON template'}), 500

# Validation endpoints
@export_import_bp.route('/assets/import/validate', methods=['POST'])
@token_required
def validate_import_file(user):
    """Validate import file without importing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        format_type = request.form.get('format_type')
        if not format_type:
            # Detect format from file extension
            filename = file.filename.lower()
            if filename.endswith('.csv'):
                format_type = 'csv'
            elif filename.endswith('.json'):
                format_type = 'json'
            else:
                return jsonify({'error': 'Unable to determine file format'}), 400
        
        validation = AssetExportService.validate_import_data(file, format_type)
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to validate import file'}), 500

# Format information endpoints
@export_import_bp.route('/assets/export/formats', methods=['GET'])
@token_required
def get_export_formats(user):
    """Get available export formats"""
    try:
        formats = AssetExportService.get_export_formats()
        return jsonify({'export_formats': formats}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch export formats'}), 500

@export_import_bp.route('/assets/import/formats', methods=['GET'])
@token_required
def get_import_formats(user):
    """Get available import formats"""
    try:
        formats = AssetExportService.get_import_formats()
        return jsonify({'import_formats': formats}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch import formats'}), 500

# Bulk operations
@export_import_bp.route('/assets/export/bulk', methods=['POST'])
@token_required
def bulk_export_assets(user):
    """Export assets for multiple grants"""
    try:
        data = request.get_json()
        grant_ids = data.get('grant_ids', [])
        format_type = data.get('format', 'csv')
        include_details = data.get('include_details', True)
        
        if not grant_ids:
            return jsonify({'error': 'Grant IDs are required'}), 400
        
        bulk_exports = []
        
        for grant_id in grant_ids:
            try:
                if format_type == 'csv':
                    export_data = AssetExportService.export_assets_to_csv(grant_id, include_details)
                elif format_type == 'json':
                    export_data = AssetExportService.export_assets_to_json(grant_id, include_details)
                else:
                    export_data = AssetExportService.export_assets_to_excel(grant_id, include_details)
                
                bulk_exports.append({
                    'grant_id': grant_id,
                    'filename': export_data['filename'],
                    'record_count': export_data['record_count'],
                    'content': export_data['content']
                })
                
            except Exception as e:
                bulk_exports.append({
                    'grant_id': grant_id,
                    'error': str(e)
                })
        
        return jsonify({
            'message': 'Bulk export completed',
            'exports': bulk_exports,
            'total_grants': len(grant_ids),
            'successful': len([e for e in bulk_exports if 'error' not in e]),
            'failed': len([e for e in bulk_exports if 'error' in e])
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to perform bulk export'}), 500

@export_import_bp.route('/assets/import/bulk', methods=['POST'])
@token_required
def bulk_import_assets(user):
    """Import assets for multiple grants"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        update_existing = request.form.get('update_existing', 'false').lower() == 'true'
        
        bulk_imports = []
        
        for file in files:
            try:
                # Determine grant ID from filename or form data
                grant_id = request.form.get(f'grant_id_{file.filename}')
                if not grant_id:
                    # Try to extract from filename (e.g., assets_grant_1.csv)
                    import re
                    match = re.search(r'grant_(\d+)', file.filename)
                    if match:
                        grant_id = int(match.group(1))
                    else:
                        bulk_imports.append({
                            'filename': file.filename,
                            'error': 'Unable to determine grant ID'
                        })
                        continue
                
                grant_id = int(grant_id)
                
                # Determine format
                format_type = 'csv' if file.filename.lower().endswith('.csv') else 'json'
                
                # Import file
                if format_type == 'csv':
                    results = AssetExportService.import_assets_from_csv(file, grant_id, user.id, update_existing)
                else:
                    results = AssetExportService.import_assets_from_json(file, grant_id, user.id, update_existing)
                
                bulk_imports.append({
                    'filename': file.filename,
                    'grant_id': grant_id,
                    'results': results
                })
                
            except Exception as e:
                bulk_imports.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return jsonify({
            'message': 'Bulk import completed',
            'imports': bulk_imports,
            'total_files': len(files),
            'successful': len([i for i in bulk_imports if 'error' not in i]),
            'failed': len([i for i in bulk_imports if 'error' in i])
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to perform bulk import'}), 500

# Preview endpoints
@export_import_bp.route('/assets/import/preview', methods=['POST'])
@token_required
def preview_import_file(user):
    """Preview import file data without importing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        format_type = request.form.get('format_type')
        if not format_type:
            filename = file.filename.lower()
            if filename.endswith('.csv'):
                format_type = 'csv'
            elif filename.endswith('.json'):
                format_type = 'json'
            else:
                return jsonify({'error': 'Unable to determine file format'}), 400
        
        # Read and preview data
        preview_data = {
            'format': format_type,
            'filename': file.filename,
            'sample_rows': [],
            'total_rows': 0
        }
        
        if format_type == 'csv':
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            preview_data['headers'] = csv_reader.fieldnames
            preview_data['total_rows'] = len(list(csv_reader))
            
            # Reset file position and read sample rows
            file.seek(0)
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for i, row in enumerate(csv_reader):
                if i >= 5:  # Limit to 5 sample rows
                    break
                preview_data['sample_rows'].append(row)
        
        elif format_type == 'json':
            json_content = file.read().decode('utf-8')
            data = json.loads(json_content)
            
            assets_data = data.get('assets', [])
            preview_data['total_rows'] = len(assets_data)
            
            # Add sample rows
            for i, asset_data in enumerate(assets_data):
                if i >= 5:
                    break
                preview_data['sample_rows'].append(asset_data)
        
        return jsonify(preview_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to preview import file'}), 500

# Export history (placeholder)
@export_import_bp.route('/assets/export/history', methods=['GET'])
@token_required
def get_export_history(user):
    """Get export history (placeholder)"""
    try:
        # This would query an export history table
        history = [
            {
                'id': 1,
                'grant_id': 1,
                'format': 'csv',
                'record_count': 25,
                'exported_at': '2025-03-20T10:00:00',
                'exported_by': user.id
            },
            {
                'id': 2,
                'grant_id': 1,
                'format': 'json',
                'record_count': 25,
                'exported_at': '2025-03-15T14:30:00',
                'exported_by': user.id
            }
        ]
        
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch export history'}), 500

# Import history (placeholder)
@export_import_bp.route('/assets/import/history', methods=['GET'])
@token_required
def get_import_history(user):
    """Get import history (placeholder)"""
    try:
        # This would query an import history table
        history = [
            {
                'id': 1,
                'grant_id': 1,
                'format': 'csv',
                'imported_count': 10,
                'updated_count': 5,
                'error_count': 0,
                'imported_at': '2025-03-20T11:00:00',
                'imported_by': user.id
            },
            {
                'id': 2,
                'grant_id': 2,
                'format': 'json',
                'imported_count': 15,
                'updated_count': 3,
                'error_count': 2,
                'imported_at': '2025-03-18T16:45:00',
                'imported_by': user.id
            }
        ]
        
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch import history'}), 500
