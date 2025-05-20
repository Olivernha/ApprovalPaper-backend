from fastapi import HTTPException, status
from typing import List, Union, Optional
from app.schema.base import PyObjectId
from app.schema.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentDelete,
    DocumentResponse,
    DocumentUpdateNormal,
    DocumentUpdateAdmin,
    DocumentPaginationResponse,
)
from app.services.documentService import DocumentService

class DocumentController:
    @staticmethod
    async def get_documents() -> List[DocumentResponse]:
        try:
            return await DocumentService().get_documents()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def get_documents_paginated(
        page: int = 1, 
        limit: int = 10, 
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        department_id: Optional[str] = None,
        document_type_id: Optional[str] = None,
        sort_field: str = "created_date",
        sort_order: int = -1
    ) -> DocumentPaginationResponse:
        try:
            return await DocumentService().get_documents_paginated(
                page=page,
                limit=limit,
                search=search,
                status_filter=status_filter,
                department_id=department_id,
                document_type_id=document_type_id,
                sort_field=sort_field,
                sort_order=sort_order
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def create_document(document: DocumentCreate) -> DocumentResponse:
        try:
            return await DocumentService().create_document(document)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def update_document(
        doc_id: PyObjectId,
        update_data: Union[DocumentUpdateNormal, DocumentUpdateAdmin]
    ) -> DocumentResponse:
        try:
            return await DocumentService().update_document(str(doc_id), update_data)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def delete_document(
        document_id: PyObjectId,
        document_delete: DocumentDelete,
    ) -> dict:
        try:
            return await DocumentService().delete_document(str(document_id), document_delete.current_user)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    @staticmethod
    async def bulk_delete_documents(
        bulk_delete: BulkDeleteRequest,
    ) -> dict:
        try:
            return await DocumentService().bulk_delete_documents(bulk_delete)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def bulk_update_status(
        bulk_update: BulkUpdateStatusRequest,
    ) -> dict:
        try:
            return await DocumentService().bulk_update_status(bulk_update)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))