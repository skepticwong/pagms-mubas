"""
Asset Document Routes - Document management endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from middleware.auth import token_required
from werkzeug.datastructures import FileStorage
from services.asset_document_service import AssetDocumentService
from models import Asset
import os

documents_bp = Blueprint('asset_file_mgmt', __name__)

@documents_bp.route('/assets/<int:asset_id>/documents', methods=['POST'])
@token_required
def upload_document(user, asset_id):
    """Upload document for an asset"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get document metadata
        document_data = {
            'category': request.form.get('category', 'Other'),
            'description': request.form.get('description', ''),
            'expires_at': request.form.get('expires_at'),
            'is_confidential': request.form.get('is_confidential', 'false').lower() == 'true'
        }
        
        # Upload document
        document = AssetDocumentService.upload_asset_document(asset_id, file, document_data, user.id)
        
        return jsonify({
            'message': 'Document uploaded successfully',
            'document': document
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to upload document'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents', methods=['GET'])
@token_required
def get_asset_documents(user, asset_id):
    """Get all documents for an asset"""
    try:
        category = request.args.get('category')
        documents = AssetDocumentService.get_asset_documents(asset_id, category)
        
        return jsonify({'documents': documents}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch documents'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/<document_id>', methods=['GET'])
@token_required
def get_document(user, asset_id, document_id):
    """Get specific document details"""
    try:
        document = AssetDocumentService.get_document_by_id(asset_id, document_id)
        return jsonify({'document': document}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch document'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/<document_id>/download', methods=['GET'])
@token_required
def download_document(user, asset_id, document_id):
    """Download a document"""
    try:
        document = AssetDocumentService.get_document_by_id(asset_id, document_id)
        file_path = document['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=document['filename'],
            mimetype=document['mime_type']
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to download document'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/<document_id>', methods=['PUT'])
@token_required
def update_document(user, asset_id, document_id):
    """Update document metadata"""
    try:
        metadata = request.get_json()
        document = AssetDocumentService.update_document_metadata(asset_id, document_id, metadata, user.id)
        
        return jsonify({
            'message': 'Document updated successfully',
            'document': document
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update document'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/<document_id>', methods=['DELETE'])
@token_required
def delete_document(user, asset_id, document_id):
    """Delete a document"""
    try:
        success = AssetDocumentService.delete_document(asset_id, document_id, user.id)
        
        if success:
            return jsonify({'message': 'Document deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete document'}), 400
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to delete document'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/<document_id>/versions', methods=['POST'])
@token_required
def create_document_version(user, asset_id, document_id):
    """Create a new version of an existing document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get version data
        version_data = {
            'description': request.form.get('description', ''),
            'expires_at': request.form.get('expires_at'),
            'version_notes': request.form.get('version_notes', '')
        }
        
        # Create new version
        new_version = AssetDocumentService.create_document_version(asset_id, document_id, file, version_data, user.id)
        
        return jsonify({
            'message': 'Document version created successfully',
            'document': new_version
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create document version'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/<document_id>/versions', methods=['GET'])
@token_required
def get_document_versions(user, asset_id, document_id):
    """Get all versions of a document"""
    try:
        versions = AssetDocumentService.get_document_versions(asset_id, document_id)
        return jsonify({'versions': versions}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch document versions'}), 500

@documents_bp.route('/assets/documents/search', methods=['POST'])
@token_required
def search_documents(user):
    """Search documents across all assets in a grant"""
    try:
        search_criteria = request.get_json()
        grant_id = search_criteria.get('grant_id')
        
        if not grant_id:
            return jsonify({'error': 'Grant ID is required'}), 400
        
        results = AssetDocumentService.search_documents(grant_id, search_criteria)
        
        return jsonify({'results': results, 'total': len(results)}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to search documents'}), 500

@documents_bp.route('/assets/documents/statistics/<int:grant_id>', methods=['GET'])
@token_required
def get_document_statistics(user, grant_id):
    """Get document statistics for a grant"""
    try:
        stats = AssetDocumentService.get_document_statistics(grant_id)
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch document statistics'}), 500

@documents_bp.route('/assets/documents/cleanup', methods=['POST'])
@token_required
def cleanup_expired_documents(user):
    """Clean up expired documents (admin only)"""
    try:
        if user.role not in ['RSU', 'Finance']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        result = AssetDocumentService.cleanup_expired_documents()
        
        return jsonify({
            'message': 'Cleanup completed successfully',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to cleanup documents'}), 500

@documents_bp.route('/assets/documents/categories', methods=['GET'])
@token_required
def get_document_categories(user):
    """Get available document categories"""
    try:
        categories = AssetDocumentService.get_document_categories()
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch categories'}), 500

@documents_bp.route('/assets/documents/extensions', methods=['GET'])
@token_required
def get_allowed_extensions(user):
    """Get allowed file extensions"""
    try:
        extensions = AssetDocumentService.get_allowed_extensions()
        return jsonify({'allowed_extensions': extensions}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch extensions'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/bulk-upload', methods=['POST'])
@token_required
def bulk_upload_documents(user, asset_id):
    """Upload multiple documents for an asset"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        default_category = request.form.get('default_category', 'Other')
        default_description = request.form.get('default_description', '')
        
        uploaded_documents = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                document_data = {
                    'category': request.form.get(f'category_{file.filename}', default_category),
                    'description': request.form.get(f'description_{file.filename}', default_description),
                    'expires_at': request.form.get(f'expires_at_{file.filename}'),
                    'is_confidential': request.form.get(f'confidential_{file.filename}', 'false').lower() == 'true'
                }
                
                document = AssetDocumentService.upload_asset_document(asset_id, file, document_data, user.id)
                uploaded_documents.append(document)
                
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return jsonify({
            'message': f'Uploaded {len(uploaded_documents)} documents successfully',
            'uploaded_documents': uploaded_documents,
            'errors': errors
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to upload documents'}), 500

@documents_bp.route('/assets/<int:asset_id>/documents/preview/<document_id>', methods=['GET'])
@token_required
def preview_document(user, asset_id, document_id):
    """Get document preview (for images and PDFs)"""
    try:
        document = AssetDocumentService.get_document_by_id(asset_id, document_id)
        file_path = document['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file is previewable
        previewable_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        
        if document['mime_type'] not in previewable_types:
            return jsonify({'error': 'File type not previewable'}), 400
        
        return send_file(file_path, mimetype=document['mime_type'])
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to preview document'}), 500

@documents_bp.route('/assets/documents/expiring-soon/<int:grant_id>', methods=['GET'])
@token_required
def get_expiring_documents(user, grant_id):
    """Get documents expiring soon"""
    try:
        stats = AssetDocumentService.get_document_statistics(grant_id)
        expiring_docs = stats.get('expiring_soon', [])
        
        return jsonify({'expiring_documents': expiring_docs}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch expiring documents'}), 500

@documents_bp.route('/assets/documents/recent-uploads/<int:grant_id>', methods=['GET'])
@token_required
def get_recent_uploads(user, grant_id):
    """Get recently uploaded documents"""
    try:
        stats = AssetDocumentService.get_document_statistics(grant_id)
        recent_docs = stats.get('recent_uploads', [])
        
        return jsonify({'recent_uploads': recent_docs}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recent uploads'}), 500
