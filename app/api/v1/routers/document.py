
from datetime import datetime
from fastapi import APIRouter, Path, Query, Form, File, UploadFile, Depends, HTTPException, status
from typing import Dict, List, Optional

from motor.motor_asyncio import  AsyncIOMotorGridFSBucket
from starlette.responses import FileResponse

from app.api.v1.controllers.document import DocumentController
from app.core.database import MongoDB
from app.core.dependencies.auth import get_current_user_from_header
from app.core.dependencies.document import get_document_service
from app.schemas.admin import AuthInAdminDB
from app.schemas.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentResponse,
    DocumentPaginationResponse,
    DocumentUpdateNormal,
    DocumentUpdateAdmin,
)
from app.schemas.base import PyObjectId

from app.core.utils import  to_object_id
from app.core.config import settings
from app.services.FileStorageService import FileStorageService
from app.services.document import DocumentService

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/document",
    tags=["document"],
    responses={404: {"description": "Not found"}},
)



async def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    db = MongoDB.get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not established")
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name=settings.GRIDFS_BUCKET_NAME)
    return bucket


@router.get("/", response_model=List[DocumentResponse])
async def get_documents():
    return await DocumentController.get_documents()


@router.get('/search')
async def search_documents(
        search: Optional[str] = Query(None, description="Search query for title, ref_no, or created_by"),
        status: Optional[str] = Query(None, description="Filter by document status (Not Filed, Filed, Suspended)"),
):
    return await DocumentController.get_documents_search(search,status_filter=status)


@router.get("/paginated", response_model=DocumentPaginationResponse)
async def get_documents_paginated(
        page: int = Query(1, ge=1, description="Page number, starting from 1"),
        limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
        search: Optional[str] = Query(None, description="Search query for title, ref_no, or created_by"),
        status: Optional[str] = Query(None, description="Filter by document status (Not Filed, Filed, Suspended)"),
        department_id: Optional[str] = Query(None, description="Filter by department ID"),
        document_type_id: Optional[str] = Query(None, description="Filter by document type ID"),
        sort_field: str = Query("created_date", description="Field to sort by"),
        sort_order: int = Query(-1, description="Sort order: 1 for ascending, -1 for descending")
):

    return await DocumentController.get_documents_paginated(
        page=page,
        limit=limit,
        search=search,
        status_filter=status,
        department_id=department_id,
        document_type_id=document_type_id,
        sort_field=sort_field,
        sort_order=sort_order
    )
@router.get("/count_status/{department_id}", response_model=Dict[str, int])
async def count_docs_by_status(department_id: str = Path(..., title="Department ID", description="The ObjectId of the department")):
    return await DocumentController.count_docs_by_status(department_id)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str = Path(..., title="Document ID", description="The ObjectId of the document")):
    return await DocumentController.get_document_by_id(document_id)

@router.get('/name/{document_title}', response_model=DocumentResponse)
async def get_document_by_name(document_title: str = Path(..., title="Document title", description="The name of the document")):
    return await DocumentController.get_document_by_name(document_title)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def create_document(document: DocumentCreate, current_user: AuthInAdminDB = Depends(get_current_user_from_header)):
    print(document , current_user)
    return await DocumentController.create_document(document, current_user)

@router.put("/{doc_id}", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def update_document(
        doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document"),
        title: Optional[str] = Form(None, min_length=1),
        document_type_id: Optional[PyObjectId] = Form(None),
        department_id: Optional[PyObjectId] = Form(None),
        file_id: Optional[PyObjectId] = Form(None),
        doc_status: Optional[str] = Form(None, pattern="^(Not Filed|Filed|Suspended)$"),
        created_date: Optional[str] = Form(None),
        created_by: Optional[str] = Form(None),
        filed_date: Optional[str] = Form(None),
        filed_by: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None, description="File to upload"),
        current_user_data: AuthInAdminDB = Depends(get_current_user_from_header),
):
    is_admin = current_user_data.is_admin
    if is_admin:
        created_date = datetime.fromisoformat(created_date) if created_date else None
        filed_date = datetime.fromisoformat(filed_date) if filed_date else None
        update_data = DocumentUpdateAdmin(
            doc_id=doc_id,
            title=title,
            document_type_id=document_type_id,
            department_id=department_id,
            status=doc_status,
            created_date=created_date,
            created_by=created_by,
            filed_date=filed_date,
            filed_by=filed_by,
        )
    else:
        update_data = DocumentUpdateNormal(
            doc_id=doc_id,
            title=title,
            document_type_id=document_type_id,
            department_id=department_id,
        )

    return await DocumentController.update_document(update_data, current_user_data,file)

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
        document_id: str = Path(..., title="Document ID", description="The ObjectId of the document"),
        current_user: AuthInAdminDB = Depends(get_current_user_from_header)
) -> dict:
    return await DocumentController.delete_document(document_id, current_user)

@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_documents(bulk_delete: BulkDeleteRequest, current_user_data: AuthInAdminDB = Depends(get_current_user_from_header)):
    return await DocumentController.bulk_delete_documents(bulk_delete, current_user_data)

@router.post("/bulk-update-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(bulk_update: BulkUpdateStatusRequest, current_user_data: AuthInAdminDB = Depends(get_current_user_from_header)):
    return await DocumentController.bulk_update_status(bulk_update, current_user_data)

@router.get("/{doc_id}/file")
async def get_document_file(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    print('DOCUMENT', doc_id)
    document = await document_service.get_collection().find_one({"_id": to_object_id(doc_id)})
    print('Document', document)
    if not document or not document.get("file_path"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file_storage = FileStorageService()
    file_path = file_storage.get_file_path(document["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on storage")

    return FileResponse(file_path)