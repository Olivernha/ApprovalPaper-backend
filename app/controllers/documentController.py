from typing import List
from fastapi import HTTPException, status
from app.services.documentService import DocumentService
from app.schema.document import DocumentCreate, DocumentInDB, DocumentUpdateNormal, DocumentUpdateAdmin
from app.schema.base import PyObjectId

class DocumentController:
    COLLECTION_NAME = "documents"
    @staticmethod
    async def create_document(document: DocumentCreate, collection_name: str = COLLECTION_NAME) -> DocumentInDB:
        try:
            service = DocumentService(collection_name=collection_name)
            created_document = await service.create_document(document)
            return created_document
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    @staticmethod
    async def get_documents(collection_name: str = COLLECTION_NAME) -> List[DocumentInDB]:
        try:
            service = DocumentService(collection_name=collection_name)
            return await service.get_documents()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    @staticmethod
    async def verify_document_by_created_by(doc_id: str, username: str) -> bool:
        try:
            service = DocumentService()
            user = await service.is_your_document(doc_id, username)
            if not user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User did not create this document")
            return True
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def update_document(
        document_id: PyObjectId,
        update_data: DocumentUpdateNormal | DocumentUpdateAdmin,
        collection_name: str = COLLECTION_NAME
    ) -> dict:
        try:
            service = DocumentService(collection_name=collection_name)
            return await service.update_document(document_id, update_data)
        except Exception:
            raise 