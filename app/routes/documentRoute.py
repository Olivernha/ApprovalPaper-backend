from fastapi import APIRouter, HTTPException, Path, Query, Request, status, Form, File, UploadFile, Depends
from fastapi.responses import StreamingResponse
from typing import List, Union, Optional
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from app.controllers.documentController import DocumentController
from app.database import MongoDB
from app.dependencies.auth import get_current_user_from_header
from app.schema.admin import AuthInAdminDB
from app.schema.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentResponse,
    DocumentPaginationResponse,
    DocumentUpdateNormal,
    DocumentUpdateAdmin,
)
from app.schema.base import PyObjectId
from app.config.settings import settings
from bson.errors import InvalidId
from fastapi.responses import StreamingResponse
from app.services.adminService import AdminService

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/document",
    tags=["document"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get GridFS bucket
async def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    db = MongoDB.get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection not established")
    return AsyncIOMotorGridFSBucket(db,bucket_name=settings.GRIDFS_BUCKET_NAME)

@router.get("/", response_model=List[DocumentResponse])
async def get_documents():
    try:
        return await DocumentController.get_documents()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
    try:
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
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def create_document(document: DocumentCreate, current_user: AuthInAdminDB = Depends(get_current_user_from_header)):
    try:
        return await DocumentController.create_document(document, current_user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{doc_id}", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def update_document(
        current_user_data: AuthInAdminDB = Depends(get_current_user_from_header),
        doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document"),
        title: Optional[str] = Form(None, min_length=1, max_length=200),
        document_type_id: Optional[PyObjectId] = Form(None),
        department_id: Optional[PyObjectId] = Form(None),
        doc_status: Optional[str] = Form(None, pattern="^(Not Filed|Filed|Suspended)$"),
        created_date: Optional[str] = Form(None),
        created_by: Optional[str] = Form(None),
        filed_date: Optional[str] = Form(None),
        filed_by: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None, description="File to upload"),
        gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
):
    """
    Update a document with optional file upload to GridFS
    - For admin users, all fields are required.
    - For normal users, only title, document_type_id, and department_id are required.
    - The file is optional and can be uploaded in various formats (PDF, DOCX, TXT, JPEG, PNG).
    """
    try:
        is_admin = current_user_data.is_admin
        if is_admin:
            update_data = DocumentUpdateAdmin(
                doc_id=doc_id,
                title=title,
                document_type_id=PyObjectId(document_type_id),
                department_id=PyObjectId(department_id),
                status=doc_status,
                created_date=created_date,
                created_by=created_by,
                filed_date=filed_date,
                filed_by=filed_by
            )
        else:
            update_data = DocumentUpdateNormal(
                doc_id=doc_id,
                title=title,
                document_type_id=PyObjectId(document_type_id),
                department_id=PyObjectId(department_id),
            )

        # Handle file upload
        file_id = None

        if file:
            # IMAGE ALLOWED
            allowed_types = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  
                "text/plain",
                "image/jpeg",
                "image/png",
                "image/jpg",
            ]
            if file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")

            max_size = 10 * 1024 * 1024  # 10MB
            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

            try:
                file_id = await gridfs_bucket.upload_from_stream(
                    filename=file.filename,
                    source=content,
                    metadata={"content_type": file.content_type}
                )
                update_data.file_id = str(file_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"GridFS upload failed: {str(e)}")

        try:
            updated_doc = await DocumentController.update_document(update_data, current_user_data)
            return updated_doc
        except Exception as e:
            if file_id:
                await gridfs_bucket.delete(file_id)
            raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
        document_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document"),
        current_user: AuthInAdminDB = Depends(get_current_user_from_header)
) -> dict:
    try:
        return await DocumentController.delete_document(document_id, current_user)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_documents(bulk_delete: BulkDeleteRequest, current_user_data: AuthInAdminDB = Depends(get_current_user_from_header)):
    try:
        return await DocumentController.bulk_delete_documents(bulk_delete, current_user_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk-update-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(bulk_update: BulkUpdateStatusRequest, current_user_data: AuthInAdminDB = Depends(get_current_user_from_header)):
    try:
        return await DocumentController.bulk_update_status(bulk_update, current_user_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
