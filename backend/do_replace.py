import os

files = [
    'verify_logic.py',
    'check_tasks_evidence.py',
    'services/report_service.py',
    'services/effort_service.py',
    'services/document_service.py',
    'services/grant_service.py',
    'models.py',
    'app.py'
]

replacements = {
    'EvidenceSubmission': 'DeliverableSubmission',
    'evidence_submissions': 'deliverable_submissions',
    'evidence_filename': 'deliverable_filename',
    'evidence_url': 'deliverable_url',
    'Evidence Document': 'Deliverable Document',
    'Evidence Photo': 'Deliverable Photo',
    'Milestone Evidence': 'Milestone Deliverable',
    'milestone_evidence_': 'milestone_deliverable_',
    'evidence_file': 'deliverable_file',
    'verify_evidence': 'verify_deliverable',
    'evidence': 'deliverable',
    'Evidence': 'Deliverable'
}

cwd = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend'
log_file = os.path.join(cwd, 'result.log')

with open(log_file, 'w', encoding='utf-8') as log:
    for file in files:
        filepath = os.path.join(cwd, file.replace('/', '\\'))
        if not os.path.exists(filepath):
            log.write(f"Not found: {filepath}\n")
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            for old, new in replacements.items():
                content = content.replace(old, new)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            log.write(f"Success: {filepath}\n")
        except Exception as e:
            log.write(f"Error: {filepath} - {str(e)}\n")

    log.write("Done.\n")
