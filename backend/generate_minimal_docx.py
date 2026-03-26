import zipfile
import os
import io

def create_minimal_docx(path):
    # Minimal XML content for a docx file
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
    
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        '<w:p><w:r><w:t>Generic Report Template</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>This is a placeholder template for PAGMS.</w:t></w:r></w:p>'
        '</w:body>'
        '</w:document>'
    )

    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with zipfile.ZipFile(path, 'w') as docx:
        docx.writestr('[Content_Types].xml', content_types)
        docx.writestr('_rels/.rels', rels)
        docx.writestr('word/document.xml', document_xml)

if __name__ == '__main__':
    target_path = os.path.join('templates', 'reports', 'generic.docx')
    try:
        create_minimal_docx(target_path)
        print(f"SUCCESS: Created {target_path}")
    except Exception as e:
        print(f"ERROR: {e}")
