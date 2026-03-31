"""
Asset Document Service - Document management for assets
Handles document upload, storage, versioning, and retrieval for assets
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
from models import db, Asset, User
from services.notification_service import NotificationService

class AssetDocumentService:
    """Service for managing asset documents"""
    
    # Allowed document types
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
        'txt', 'csv', 'zip', 'rar'
    }
    
    # Document categories
    DOCUMENT_CATEGORIES = [
        'Purchase Receipt',
        'Invoice',
        'Warranty',
        'User Manual',
        'Maintenance Record',
        'Inspection Report',
        'Insurance',
        'Lending Agreement',
        'Transfer Document',
        'Disposition Form',
        'Photo',
        'Other'
    ]
    
    @staticmethod
    def upload_asset_document(asset_id: int, file, document_data: Dict, user_id: int) -> Dict:
        """Upload document for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Validate file
        if not AssetDocumentService._validate_file(file):
            raise ValueError("Invalid file type or size")
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create upload directory
        upload_dir = os.path.join('uploads', 'asset_documents', str(asset_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Create document record
        document = {
            'id': str(uuid.uuid4()),
            'filename': filename,
            'unique_filename': unique_filename,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'mime_type': file.content_type,
            'category': document_data.get('category', 'Other'),
            'description': document_data.get('description', ''),
            'version': 1,
            'uploaded_by': user_id,
            'uploaded_at': datetime.utcnow().isoformat(),
            'expires_at': document_data.get('expires_at'),
            'is_confidential': document_data.get('is_confidential', False)
        }
        
        # Add to asset's supporting documents
        if not asset.supporting_documents:
            asset.supporting_documents = {}
        
        if 'documents' not in asset.supporting_documents:
            asset.supporting_documents['documents'] = []
        
        asset.supporting_documents['documents'].append(document)
        asset.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Create notification for important documents
        if document['category'] in ['Warranty', 'Insurance', 'Lending Agreement']:
            AssetDocumentService._create_document_notification(asset, document, user_id)
        
        return document
    
    @staticmethod
    def get_asset_documents(asset_id: int, category: str = None) -> List[Dict]:
        """Get all documents for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
        
        if category:
            documents = [doc for doc in documents if doc.get('category') == category]
        
        # Sort by upload date (newest first)
        documents.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
        
        return documents
    
    @staticmethod
    def get_document_by_id(asset_id: int, document_id: str) -> Dict:
        """Get specific document by ID"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
        
        for document in documents:
            if document.get('id') == document_id:
                return document
        
        raise ValueError("Document not found")
    
    @staticmethod
    def update_document_metadata(asset_id: int, document_id: str, metadata: Dict, user_id: int) -> Dict:
        """Update document metadata"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
        
        for document in documents:
            if document.get('id') == document_id:
                # Update allowed fields
                if 'category' in metadata:
                    document['category'] = metadata['category']
                if 'description' in metadata:
                    document['description'] = metadata['description']
                if 'expires_at' in metadata:
                    document['expires_at'] = metadata['expires_at']
                if 'is_confidential' in metadata:
                    document['is_confidential'] = metadata['is_confidential']
                
                document['updated_by'] = user_id
                document['updated_at'] = datetime.utcnow().isoformat()
                
                asset.updated_at = datetime.utcnow()
                db.session.commit()
                
                return document
        
        raise ValueError("Document not found")
    
    @staticmethod
    def delete_document(asset_id: int, document_id: str, user_id: int) -> bool:
        """Delete a document"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
        
        for i, document in enumerate(documents):
            if document.get('id') == document_id:
                # Delete physical file
                try:
                    os.remove(document['file_path'])
                except:
                    pass  # File might not exist
                
                # Remove from documents list
                documents.pop(i)
                asset.supporting_documents['documents'] = documents
                asset.updated_at = datetime.utcnow()
                
                db.session.commit()
                return True
        
        raise ValueError("Document not found")
    
    @staticmethod
    def create_document_version(asset_id: int, document_id: str, file, version_data: Dict, user_id: int) -> Dict:
        """Create a new version of an existing document"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Get original document
        original_doc = AssetDocumentService.get_document_by_id(asset_id, document_id)
        
        # Validate new file
        if not AssetDocumentService._validate_file(file):
            raise ValueError("Invalid file type or size")
        
        # Generate new filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_v{original_doc.get('version', 1) + 1}_{filename}"
        
        # Save new file
        upload_dir = os.path.join('uploads', 'asset_documents', str(asset_id))
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Create new version
        new_version = {
            'id': str(uuid.uuid4()),
            'filename': filename,
            'unique_filename': unique_filename,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'mime_type': file.content_type,
            'category': original_doc.get('category', 'Other'),
            'description': version_data.get('description', f"Version {original_doc.get('version', 1) + 1}"),
            'version': original_doc.get('version', 1) + 1,
            'uploaded_by': user_id,
            'uploaded_at': datetime.utcnow().isoformat(),
            'expires_at': version_data.get('expires_at'),
            'is_confidential': original_doc.get('is_confidential', False),
            'parent_document_id': document_id,
            'version_notes': version_data.get('version_notes', '')
        }
        
        # Add to documents list
        documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
        documents.append(new_version)
        asset.supporting_documents['documents'] = documents
        asset.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return new_version
    
    @staticmethod
    def get_document_versions(asset_id: int, document_id: str) -> List[Dict]:
        """Get all versions of a document"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
        
        versions = []
        for doc in documents:
            if doc.get('id') == document_id or doc.get('parent_document_id') == document_id:
                versions.append(doc)
        
        # Sort by version number
        versions.sort(key=lambda x: x.get('version', 0))
        
        return versions
    
    @staticmethod
    def search_documents(grant_id: int, search_criteria: Dict) -> List[Dict]:
        """Search documents across all assets in a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        results = []
        search_term = search_criteria.get('search_term', '').lower()
        category = search_criteria.get('category')
        date_from = search_criteria.get('date_from')
        date_to = search_criteria.get('date_to')
        
        for asset in assets:
            documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
            
            for document in documents:
                matches = True
                
                # Search term
                if search_term:
                    term_matches = (
                        search_term in document.get('filename', '').lower() or
                        search_term in document.get('description', '').lower()
                    )
                    if not term_matches:
                        matches = False
                
                # Category
                if category and document.get('category') != category:
                    matches = False
                
                # Date range
                if date_from or date_to:
                    upload_date = datetime.fromisoformat(document.get('uploaded_at', '')).date()
                    if date_from and upload_date < datetime.fromisoformat(date_from).date():
                        matches = False
                    if date_to and upload_date > datetime.fromisoformat(date_to).date():
                        matches = False
                
                if matches:
                    results.append({
                        'document': document,
                        'asset': {
                            'id': asset.id,
                            'name': asset.name,
                            'asset_tag': asset.asset_tag
                        }
                    })
        
        return results
    
    @staticmethod
    def get_document_statistics(grant_id: int) -> Dict:
        """Get document statistics for a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        stats = {
            'total_documents': 0,
            'total_size': 0,
            'by_category': {},
            'by_asset': {},
            'recent_uploads': [],
            'expiring_soon': [],
            'storage_usage': 0
        }
        
        for asset in assets:
            documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
            
            asset_docs = 0
            for document in documents:
                stats['total_documents'] += 1
                stats['total_size'] += document.get('file_size', 0)
                asset_docs += 1
                
                # Category stats
                category = document.get('category', 'Other')
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                
                # Recent uploads (last 7 days)
                upload_date = datetime.fromisoformat(document.get('uploaded_at', ''))
                if upload_date > datetime.utcnow() - timedelta(days=7):
                    stats['recent_uploads'].append({
                        'document': document,
                        'asset_name': asset.name
                    })
                
                # Expiring soon
                if document.get('expires_at'):
                    expiry_date = datetime.fromisoformat(document['expires_at'])
                    if expiry_date <= datetime.utcnow() + timedelta(days=30):
                        stats['expiring_soon'].append({
                            'document': document,
                            'asset_name': asset.name,
                            'days_until_expiry': (expiry_date - datetime.utcnow()).days
                        })
            
            if asset_docs > 0:
                stats['by_asset'][asset.id] = {
                    'name': asset.name,
                    'document_count': asset_docs
                }
        
        # Calculate storage usage in MB
        stats['storage_usage'] = round(stats['total_size'] / (1024 * 1024), 2)
        
        return stats
    
    @staticmethod
    def cleanup_expired_documents() -> Dict:
        """Clean up expired documents"""
        assets = Asset.query.all()
        cleaned_up = 0
        
        for asset in assets:
            documents = asset.supporting_documents.get('documents', []) if asset.supporting_documents else []
            
            for document in documents[:]:  # Copy list to allow modification
                if document.get('expires_at'):
                    expiry_date = datetime.fromisoformat(document['expires_at'])
                    if expiry_date < datetime.utcnow():
                        # Delete expired document
                        try:
                            os.remove(document['file_path'])
                        except:
                            pass
                        
                        documents.remove(document)
                        cleaned_up += 1
            
            if documents:
                asset.supporting_documents['documents'] = documents
            else:
                asset.supporting_documents = {}
        
        db.session.commit()
        
        return {
            'cleaned_up_count': cleaned_up,
            'cleanup_date': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _validate_file(file) -> bool:
        """Validate uploaded file"""
        # Check file extension
        if '.' not in file.filename:
            return False
        
        extension = file.filename.rsplit('.', 1)[1].lower()
        if extension not in AssetDocumentService.ALLOWED_EXTENSIONS:
            return False
        
        # Check file size (10MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return False
        
        return True
    
    @staticmethod
    def _create_document_notification(asset, document, user_id):
        """Create notification for important document"""
        grant = asset.grant
        if grant and grant.pi_id:
            NotificationService.create_notification(
                user_id=grant.pi_id,
                title=f'Important Document Uploaded: {document["filename"]}',
                message=f'Document "{document["filename"]}" has been uploaded for asset {asset.name}',
                type='document_upload',
                related_id=asset.id
            )
    
    @staticmethod
    def get_document_categories() -> List[str]:
        """Get available document categories"""
        return AssetDocumentService.DOCUMENT_CATEGORIES
    
    @staticmethod
    def get_allowed_extensions() -> List[str]:
        """Get allowed file extensions"""
        return AssetDocumentService.ALLOWED_EXTENSIONS
