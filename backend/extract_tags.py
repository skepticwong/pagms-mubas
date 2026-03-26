import zipfile
import re
import os

def extract_tags(docx_path):
    if not os.path.exists(docx_path):
        print(f"File not found: {docx_path}")
        return
        
    with zipfile.ZipFile(docx_path, 'r') as docx:
        content = docx.read('word/document.xml').decode('utf-8')
        
    # Find anything inside {{ }} or {% %}
    tags = re.findall(r'\{\{.*?\}\}|\{\%.*?\%\}', content)
    print("Found tags in document.xml:")
    for tag in tags:
        print(f"  {tag}")

if __name__ == '__main__':
    extract_tags('templates/reports/generic.docx')
