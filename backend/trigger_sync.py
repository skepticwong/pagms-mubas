from app import create_app
from models import db, Document
from services.document_service import DocumentService

app = create_app()

def sync():
    with app.app_context():
        print("Starting sync...")
        DocumentService.sync_legacy_documents()
        
        docs = Document.query.order_by(Document.id.desc()).limit(10).all()
        print(f"{'ID':<5} | {'Type':<20} | {'Path':<50}")
        print("-" * 80)
        for doc in docs:
            print(f"{doc.id:<5} | {doc.doc_type:<20} | {doc.file_path:<50}")
        
        print(f"\nTotal synced documents: {Document.query.count()}")

if __name__ == "__main__":
    sync()
