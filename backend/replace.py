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

cwd = r'.'

for file in files:
    filepath = os.path.join(cwd, file)
    if not os.path.exists(filepath):
        print(f"File {filepath} NOT FOUND")
        continue

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        for old, new in replacements.items():
            content = content.replace(old, new)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Replaced {filepath}")
    except Exception as e:
        print(f"Error {filepath}: {e}")

print("All done.")
