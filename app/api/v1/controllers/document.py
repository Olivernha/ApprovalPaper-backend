from typing import List, Union
from fastapi import Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.core.dependencies.auth import get_current_user_from_header
from app.schemas.base import PyObjectId
from app.services.document import DocumentService
from app.schemas.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentInDB,
    DocumentPaginationResponse,
    DocumentUpdateNormal,
    DocumentUpdateAdmin,
)
from app.schemas.admin import AuthInAdminDB


class DocumentController:
    @staticmethod
    async def get_documents() -> List[DocumentInDB]:
        return await DocumentService().get_documents()

    @staticmethod
    async def get_document_by_id(document_id: str) -> DocumentInDB:
        return await DocumentService().get_document_by_id(document_id)

    @staticmethod
    async def get_document_by_name(document_title: str) -> DocumentInDB:
        return await DocumentService().get_document_by_name(document_title)
    @staticmethod
    async def get_documents_paginated(
        page: int,
        limit: int,
        search: str | None,
        status_filter: str | None,
        department_id: str | None,
        document_type_id: str | None,
        sort_field: str,
        sort_order: int
    ) -> DocumentPaginationResponse:
        return await DocumentService().get_documents_paginated(
            page, limit, search, status_filter, department_id, document_type_id, sort_field, sort_order
        )

    
    @staticmethod
    async def create_document(document: DocumentCreate, current_user: AuthInAdminDB) -> DocumentInDB:
        document.created_by = current_user.full_name
        
        return await DocumentService().create_document(document)
 
    @staticmethod
    async def update_document(
        update_data: Union[DocumentUpdateNormal, DocumentUpdateAdmin],
        current_user_data: AuthInAdminDB
    ) -> DocumentInDB:
        print(f"Update data: {update_data}")
        return await DocumentService().update_document(update_data, current_user_data)

    @staticmethod
    async def delete_document(document_id: str, current_user: AuthInAdminDB) -> dict:
        return await DocumentService().delete_document(document_id, current_user)

    @staticmethod
    async def bulk_delete_documents(bulk_delete: BulkDeleteRequest, current_user_data: AuthInAdminDB) -> dict:
        return await DocumentService().bulk_delete_documents(bulk_delete, current_user_data)

    @staticmethod
    async def bulk_update_status(bulk_update: BulkUpdateStatusRequest, current_user_data: AuthInAdminDB) -> dict:
        return await DocumentService().bulk_update_status(bulk_update, current_user_data)
    

    async def download_document(
        document_id: str,
        current_user: AuthInAdminDB,
        gridfs_bucket: AsyncIOMotorGridFSBucket,
    ) -> StreamingResponse:
        return await DocumentService().download_document(document_id, gridfs_bucket, current_user)

    @staticmethod
    async def count_docs_by_status(department_id: str):
         """ count docs by status with department id """

         return await DocumentService().count_docs_by_status(department_id)
    
