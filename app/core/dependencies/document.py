from fastapi import Depends
from app.services.document import DocumentService

def get_document_service() -> DocumentService:
    """Dependency to provide an instance of DocumentService."""
    return DocumentService()