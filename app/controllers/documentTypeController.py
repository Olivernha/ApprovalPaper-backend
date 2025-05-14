from fastapi import HTTPException, status

from app.models import DocumentTypeModel
from ..services import DocumentTypeService
from ..schema import DocumentTypeCreate, DocumentTypeInDB

class DocumentTypeController:
    @staticmethod
    async def create_document_type(doc_type: DocumentTypeCreate, collection_name: str = DocumentTypeModel.COLLECTION_NAME) -> DocumentTypeInDB:
        try:
            service = DocumentTypeService(collection_name=collection_name)
            created_doc_type = await service.create_document_type(doc_type)
            return created_doc_type
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))