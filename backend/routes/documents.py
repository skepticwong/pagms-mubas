from flask import Blueprint, request, jsonify, session, send_from_directory
from flask_cors import CORS
from models import db, User, Grant, Document
from services.document_service import DocumentService
import os

documents_bp = Blueprint('documents', __name__)
CORS(documents_bp, origins=["http://localhost:5173"], supports_credentials=True)

@documents_bp.route('/documents', methods=['GET'])
def get_documents():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    grant_id = request.args.get('grant_id')
    
    try:
        if grant_id:
            documents = DocumentService.get_documents_for_grant(grant_id, user_id, user.role)
        else:
            documents = DocumentService.get_all_documents(user_id, user.role)
            
        return jsonify([doc.to_dict() for doc in documents]), 200
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    grant_id = request.form.get('grant_id')
    doc_type = request.form.get('doc_type')
    file = request.files.get('file')

    if not grant_id or not doc_type or not file:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        new_doc = DocumentService.upload_document(grant_id, user_id, file, doc_type)
        return jsonify(new_doc.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/documents/download/<int:doc_id>', methods=['GET'])
def download_document(doc_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    # The file_path now includes the subdirectory (e.g., 'agreements/xxx.pdf' or 'documents/xxx.pdf')
    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    return send_from_directory(uploads_dir, doc.file_path)
