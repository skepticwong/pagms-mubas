import os
import shutil
import tempfile
import zipfile
import csv
import json
from datetime import datetime
from models import db, Grant, Document, ExpenseClaim, EffortCertification, AuditLog, DeliverablesSubmission, Task

class AuditService:
    @staticmethod
    def generate_audit_package(grant_id):
        """
        Gathers all evidence, receipts, certifications and logs for a grant.
        Wraps them into a single ZIP file for RSU review.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError(f"Grant with ID {grant_id} not found.")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        package_name = f"Audit_Package_{grant.grant_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        package_path = os.path.join(temp_dir, package_name)
        os.makedirs(package_path)

        try:
            # 1. Base Folder Structure
            folders = ['Documents', 'Expenses_Receipts', 'Deliverables', 'Certifications', 'Logs']
            for folder in folders:
                os.makedirs(os.path.join(package_path, folder))

            # 2. Collect Documents (Agreements, Award Letters, etc.)
            documents = Document.query.filter_by(grant_id=grant_id).all()
            for doc in documents:
                # Assuming base path is current working directory + 'uploads'
                src_path = os.path.join(os.getcwd(), 'uploads', doc.file_path)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(package_path, 'Documents', doc.file_name))

            # 3. Collect Expense Receipts
            expenses = ExpenseClaim.query.filter_by(grant_id=grant_id, status='approved').all()
            expense_summary = []
            for exp in expenses:
                expense_summary.append(exp.to_dict())
                if exp.receipt_filename:
                    src_path = os.path.join(os.getcwd(), 'uploads', 'receipts', exp.receipt_filename)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, os.path.join(package_path, 'Expenses_Receipts', exp.receipt_filename))
            
            # Save Expense Summary CSV
            if expense_summary:
                with open(os.path.join(package_path, 'Expenses_Receipts', 'expense_summary.csv'), 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=expense_summary[0].keys())
                    writer.writeheader()
                    writer.writerows(expense_summary)

            # 4. Collect Deliverables (Photos and Docs from Submissions)
            tasks = Task.query.filter_by(grant_id=grant_id).all()
            task_ids = [t.id for t in tasks]
            external_links = []
            
            if task_ids:
                submissions = DeliverablesSubmission.query.filter(DeliverablesSubmission.task_id.in_(task_ids)).all()
                for sub in submissions:
                    task_folder = os.path.join(package_path, 'Deliverables', f'Task_{sub.task_id}')
                    os.makedirs(task_folder, exist_ok=True)
                    
                    if sub.photo_path:
                        src_path = os.path.join(os.getcwd(), 'uploads', sub.photo_path)
                        if os.path.exists(src_path):
                            # Append timestamp to filename to avoid collisions within same task folder if any, 
                            # but usually task folders are enough. Let's be safe.
                            dest_name = os.path.basename(sub.photo_path)
                            shutil.copy2(src_path, os.path.join(task_folder, dest_name))
                    
                    if sub.document_paths:
                        paths = sub.document_paths.split(',')
                        for p in paths:
                            p = p.strip()
                            if p:
                                src_path = os.path.join(os.getcwd(), 'uploads', p)
                                if os.path.exists(src_path):
                                    dest_name = os.path.basename(p)
                                    shutil.copy2(src_path, os.path.join(task_folder, dest_name))
                    
                    if sub.external_links:
                        links = sub.external_links.split(',')
                        for link in links:
                            link = link.strip()
                            if link:
                                external_links.append({
                                    'task_id': sub.task_id,
                                    'task_title': Task.query.get(sub.task_id).title if Task.query.get(sub.task_id) else 'Unknown',
                                    'url': link,
                                    'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else 'N/A'
                                })

            # Save External Links CSV
            if external_links:
                with open(os.path.join(package_path, 'Deliverables', 'external_links.csv'), 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['task_id', 'task_title', 'url', 'submitted_at'])
                    writer.writeheader()
                    writer.writerows(external_links)

            # 5. Collect Effort Certifications
            # Certifications are per user, we need to find certifications for users who worked on this grant
            # For simplicity, we'll get certifications linked to the PI and team members for the grant duration
            from models import GrantTeam
            team_members = GrantTeam.query.filter_by(grant_id=grant_id).all()
            user_ids = [grant.pi_id] + [tm.user_id for tm in team_members]
            
            certifications = EffortCertification.query.filter(
                EffortCertification.user_id.in_(user_ids),
                EffortCertification.status == 'certified'
            ).all()
            
            cert_summary = []
            for cert in certifications:
                data = cert.to_dict()
                # Filter certified_distribution to only show this grant if applicable (though currently it's a JSON string of all)
                cert_summary.append(data)
            
            if cert_summary:
                with open(os.path.join(package_path, 'Certifications', 'effort_certifications.csv'), 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=cert_summary[0].keys())
                    writer.writeheader()
                    writer.writerows(cert_summary)

            # 6. Audit Logs
            logs = AuditLog.query.filter(
                AuditLog.resource_type == 'grant',
                AuditLog.resource_id == grant_id
            ).all()
            
            log_summary = [l.to_dict() for l in logs]
            if log_summary:
                with open(os.path.join(package_path, 'Logs', 'audit_trail.csv'), 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['id', 'user_id', 'action', 'resource_type', 'resource_id', 'details', 'timestamp'])
                    writer.writeheader()
                    for log in logs:
                        writer.writerow({
                            'id': log.id,
                            'user_id': log.user_id,
                            'action': log.action,
                            'resource_type': log.resource_type,
                            'resource_id': log.resource_id,
                            'details': log.details,
                            'timestamp': log.timestamp.isoformat()
                        })

            # 6.5 metadata.json
            metadata = {
                "grant_code": grant.grant_code,
                "grant_title": grant.title,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "contents": {
                    "documents_count": len(documents),
                    "expenses_count": len(expenses),
                    "tasks_count": len(tasks),
                    "submissions_count": len(submissions) if 'submissions' in locals() else 0
                }
            }
            with open(os.path.join(package_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=4)

            # 7. Final ZIP creation
            zip_filename = f"{package_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(package_path):
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, package_path)
                        zipf.write(full_p, rel_p)

            # We'll return the path to the ZIP. 
            # Note: The caller should handle cleanup or we should move it to a persistent 'exports' folder
            exports_dir = os.path.join(os.getcwd(), 'uploads', 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            final_path = os.path.join(exports_dir, zip_filename)
            shutil.move(zip_path, final_path)
            
            return final_path

        finally:
            # Cleanup source package folder but keep the ZIP (moved)
            shutil.rmtree(temp_dir, ignore_errors=True)
