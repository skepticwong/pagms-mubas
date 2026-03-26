import zipfile
import os

def create_super_robust_docx_v3(path):
    # This version uses the flattened context names and more detailed fields
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        '<w:p><w:r><w:t>Project Report: {{ title }}</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>PI: {{ pi }}</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Period: {{ period }}</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>---</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Total Budget: {{ format_currency(total_budget) }}</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Total Spent (Spent Amount): {{ format_currency(spent_amount) }}</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>---</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Budget Breakdown by Category:</w:t></w:r></w:p>'
        '{% for cat in categories %}'
        '<w:p><w:r><w:t>- {{ cat.name }}: {{ format_currency(cat.spent) }} / {{ format_currency(cat.allocated) }}</w:t></w:r></w:p>'
        '{% endfor %}'
        '<w:p><w:r><w:t>---</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Performance Milestones:</w:t></w:r></w:p>'
        '{% for m in performance.milestones %}'
        '<w:p><w:r><w:t>- {{ m.title }} (Due: {{ m.due_date }}, Status: {{ m.status }})</w:t></w:r></w:p>'
        '{% endfor %}'
        '<w:p><w:r><w:t>---</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Generated at: {{ generated_at }}</w:t></w:r></w:p>'
        '</w:body>'
        '</w:document>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, 'w') as docx:
        docx.writestr('[Content_Types].xml', content_types)
        docx.writestr('_rels/.rels', rels)
        docx.writestr('word/document.xml', document_xml)

if __name__ == '__main__':
    target_path = os.path.join('templates', 'reports', 'generic.docx')
    try:
        create_super_robust_docx_v3(target_path)
        print(f"SUCCESS: Updated {target_path} with spent_amount and other aliases")
    except Exception as e:
        print(f"ERROR: {e}")
