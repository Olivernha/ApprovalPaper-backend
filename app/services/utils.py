from fastapi import HTTPException, status
from typing import List, Optional
from app.schemas.department import DocumentTypeCreate

def validate_document_types(new_doc_types: List[DocumentTypeCreate], existing_doc_types: Optional[List[dict]] = None) -> None:
    """Validate document types for uniqueness of names and prefixes."""
    existing_doc_types = existing_doc_types or []
    
    # Check for duplicates within new document types
    doc_type_names = {doc.name for doc in new_doc_types}
    doc_type_prefixes = {doc.prefix for doc in new_doc_types}
    if len(doc_type_names) != len(new_doc_types):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate document type names provided")
    if len(doc_type_prefixes) != len(new_doc_types):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate document type prefixes provided")
    
    # Check against existing document types
    existing_names = {doc["name"] for doc in existing_doc_types}
    existing_prefixes = {doc["prefix"] for doc in existing_doc_types}
    if any(name in existing_names for name in doc_type_names):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document type name already exists in department")
    if any(prefix in existing_prefixes for prefix in doc_type_prefixes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document type prefix already exists in department")