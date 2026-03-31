import os

search_dir = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\frontend\src"

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content.replace('Evidence', 'Deliverable')
    new_content = new_content.replace('evidence', 'deliverable')
    new_content = new_content.replace('Deliverables', 'Deliverables')
    
    # Specific component and endpoint fixes
    new_content = new_content.replace('ReviewDeliverable', 'ReviewDeliverables')
    new_content = new_content.replace('Review Deliverable', 'Review Deliverables')
    new_content = new_content.replace('review-deliverable', 'review-deliverables')
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {file_path}")

for root, dirs, files in os.walk(search_dir):
    for filename in files:
        if filename.endswith(('.svelte', '.js')):
            replace_in_file(os.path.join(root, filename))
