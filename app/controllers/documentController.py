from typing import List
from fastapi import HTTPException, status
from ..models import DocumentModel
from ..services import DocumentService
from ..schema.document import DocumentCreate, DocumentInDB

class DocumentController:
    @staticmethod
    async def create_document(document: DocumentCreate, collection_name: str = DocumentModel.COLLECTION_NAME) -> DocumentInDB:
        try:
            service = DocumentService(collection_name=collection_name)
            created_document = await service.create_document(document)
            return created_document
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    @staticmethod
    async def get_documents(collection_name: str = DocumentModel.COLLECTION_NAME) -> List[DocumentInDB]:
        try:
            service = DocumentService(collection_name=collection_name)
            return await service.get_documents()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))