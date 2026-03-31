import os
from datetime import datetime
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from models import db, Document, User, Grant, AuditLog

UPLOAD_FOLDER = 'uploads/documents'

class DocumentService:
    @staticmethod
    def upload_document(grant_id, user_id, file, doc_type):
        """
        Uploads a document, handles versioning.
        """
        if not file or not file.filename:
            raise ValueError("No file provided")

        # 1. Check for existing versions
        # Check for non-superseded documents of the same type for this grant
        existing_docs = Document.query.filter_by(
            grant_id=grant_id, 
            doc_type=doc_type, 
            is_superseded=False
        ).order_by(Document.version.desc()).all()

        version = 1
        if existing_docs:
            version = existing_docs[0].version + 1
            # Mark previous active versions as superseded
            for doc in existing_docs:
                doc.is_superseded = True
                db.session.add(doc)

        # 2. Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_v{version}_{filename}"
        
        # Save relative to backend root, consistent with GrantService
        path = os.path.join(os.getcwd(), UPLOAD_FOLDER)
        os.makedirs(path, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(os.path.join(os.getcwd(), file_path))

        # 3. Create document record
        new_doc = Document(
            grant_id=grant_id,
            uploader_id=user_id,
            file_name=filename,
            file_path=f"documents/{unique_filename}", # Use relative path from uploads/
            doc_type=doc_type,
            version=version,
            is_superseded=False
        )
        
        db.session.add(new_doc)
        
        # 4. Log Audit
        db.session.add(AuditLog(
            user_id=user_id,
            action='document_uploaded',
            resource_type='document',
            resource_id=grant_id, 
            details=f'Document "{filename}" (v{version}) uploaded for grant ID {grant_id}'
        ))
        
        db.session.commit()
        
        return new_doc

    @staticmethod
    def sync_legacy_documents(grant_id=None):
        """
        Sync files from Grant and EvidenceSubmission tables into Document table.
        This is idempotent and runs before retrieval.
        """
        from models import DeliverableSubmission, Task, Milestone

        # 1. Sync Grant files
        grants_query = Grant.query
        if grant_id:
            grants_query = grants_query.filter_by(id=grant_id)
        
        grants = grants_query.all()
        for g in grants:
            mappings = [
                (g.agreement_filename, 'Grant Agreement', 'agreements'),
                (g.award_letter_filename, 'Award Letter', 'documents'),
                (g.budget_breakdown_filename, 'Budget Breakdown', 'documents'),
                (g.ethical_approval_filename, 'Ethical Approval', 'documents'),
            ]
            
            for filename, doc_type, folder in mappings:
                if filename:
                    rel_path = f"{folder}/{filename}"
                    existing = Document.query.filter_by(grant_id=g.id, file_path=rel_path).first()
                    if not existing:
                        db.session.add(Document(
                            grant_id=g.id,
                            uploader_id=g.pi_id,
                            file_name=filename,
                            file_path=rel_path,
                            doc_type=doc_type,
                            version=1,
                            is_superseded=False,
                            created_at=g.created_at or datetime.now()
                        ))

        # 2. Sync Deliverable Submissions
        # We need to find deliverables for tasks belonging to the grant(s)
        tasks_query = Task.query
        if grant_id:
            tasks_query = tasks_query.filter_by(grant_id=grant_id)
        
        tasks = tasks_query.all()
        task_ids = [t.id for t in tasks]
        if task_ids:
            submissions = DeliverableSubmission.query.filter(DeliverableSubmission.task_id.in_(task_ids)).all()
            for sub in submissions:
                task = next((t for t in tasks if t.id == sub.task_id), None)
                if not task: continue
                
                files_to_sync = []
                # Handle comma-separated paths or JSON if it was JSON (tasks.py uses ','.join)
                if sub.document_paths:
                    paths = sub.document_paths.split(',')
                    for p in paths:
                        if p.strip():
                            files_to_sync.append((p.strip(), 'Deliverable Document'))
                
                if sub.photo_path:
                    files_to_sync.append((sub.photo_path, 'Deliverable Photo'))
                
                for filename, doc_type in files_to_sync:
                    rel_path = f"deliverables/{filename}"
                    existing = Document.query.filter_by(grant_id=task.grant_id, file_path=rel_path).first()
                    if not existing:
                        db.session.add(Document(
                            grant_id=task.grant_id,
                            uploader_id=task.assigned_to,
                            file_name=filename,
                            file_path=rel_path,
                            doc_type=doc_type,
                            version=1,
                            is_superseded=False,
                            created_at=sub.submitted_at or datetime.now()
                        ))
        
        db.session.commit()

    @staticmethod
    def get_documents_for_grant(grant_id, user_id, role):
        """
        Get documents based on roles.
        PI: All for grant.
        Team: Only own + Award Letter + final reports.
        RSU: All.
        Finance: Receipts, award letters, and budget docs.
        """
        # Sync first
        DocumentService.sync_legacy_documents(grant_id)
        
        query = Document.query.filter_by(grant_id=grant_id)
        
        if role == 'PI' or role == 'RSU':
            pass # All docs
        elif role == 'Team':
            query = query.filter(or_(
                Document.uploader_id == user_id,
                Document.doc_type.in_(['Award Letter', 'Final Report', 'Milestone Deliverable'])
            ))
        elif role == 'Finance':
            query = query.filter(Document.doc_type.in_(['Expense Receipt', 'Budget Breakdown', 'Award Letter']))
        else:
            return []

        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_all_documents(user_id, role):
        """
        Get all accessible documents across all grants.
        PI: All docs for grants where they are PI.
        Team: Docs they uploaded + specific types in grants they are part of.
        RSU: All.
        Finance: Specific types across all grants.
        """
        # Sync first
        DocumentService.sync_legacy_documents()
        
        if role == 'RSU':
            return Document.query.order_by(Document.created_at.desc()).all()
        
        if role == 'PI':
            # Documents in grants where user is PI
            return Document.query.join(Grant).filter(Grant.pi_id == user_id).order_by(Document.created_at.desc()).all()
        
        if role == 'Team':
            # Own uploads OR specific types in grants they are part of
            return Document.query.join(Grant).join(Grant.team_members).filter(
                or_(
                    Document.uploader_id == user_id,
                    db.and_(
                        Grant.team_members.any(user_id=user_id),
                        Document.doc_type.in_(['Award Letter', 'Final Report', 'Milestone Deliverable'])
                    )
                )
            ).order_by(Document.created_at.desc()).all()
            
        if role == 'Finance':
            return Document.query.filter(Document.doc_type.in_(['Expense Receipt', 'Budget Breakdown', 'Award Letter'])).order_by(Document.created_at.desc()).all()
            
        return []
