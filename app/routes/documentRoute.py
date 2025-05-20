from fastapi import APIRouter, HTTPException, Path, Query, status, Form, File, UploadFile, Depends
from fastapi.responses import StreamingResponse
from typing import List, Union, Optional
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from app.controllers.documentController import DocumentController
from app.database import MongoDB
from app.schema.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentDelete,
    DocumentResponse,
    DocumentPaginationResponse,
    DocumentUpdateNormal,
    DocumentUpdateAdmin,
)
from app.schema.base import PyObjectId
from app.config.settings import settings
import mimetypes

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
    return AsyncIOMotorGridFSBucket(db)

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
async def create_document(document: DocumentCreate):
    try:
        return await DocumentController.create_document(document)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{doc_id}", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def update_document(
        doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document"),
        title: Optional[str] = Form(None, min_length=1, max_length=200),
        document_type_id: Optional[PyObjectId] = Form(None),
        department_id: Optional[PyObjectId] = Form(None),
        doc_status: Optional[str] = Form(None, pattern="^(Not Filed|Filed|Suspended)$"),
        created_date: Optional[str] = Form(None, description="DD/MM/YYYY"),
        created_by: Optional[str] = Form(None, min_length=1),
        filed_date: Optional[str] = Form(None, description="DD/MM/YYYY"),
        filed_by: Optional[str] = Form(None, min_length=1),
        file: Optional[UploadFile] = File(None),
        current_user: str = Form(description="User who is updating the document"),
        gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
):
    """Update a document with optional file upload to GridFS"""
    try:
        # Determine update schema based on user role
        is_admin = await AdminService().is_admin(current_user)
        update_data = DocumentUpdateAdmin(
            title=title,
            document_type_id=document_type_id,
            department_id=department_id,
            status=doc_status,
            created_date=created_date,
            created_by=created_by,
            filed_date=filed_date,
            filed_by=filed_by,
            current_user=current_user
        ) if is_admin else DocumentUpdateNormal(
            title=title,
            document_type_id=document_type_id,
            department_id=department_id,
            current_user=current_user
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
            updated_doc = await DocumentController.update_document(doc_id, update_data)
            return updated_doc
        except Exception as e:
            if file_id:
                await gridfs_bucket.delete(file_id)
            raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
        document_delete: DocumentDelete,
        document_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document")
) -> dict:
    try:
        return await DocumentController.delete_document(document_id, document_delete)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_documents(bulk_delete: BulkDeleteRequest):
    try:
        return await DocumentController.bulk_delete_documents(bulk_delete)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk-update-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(bulk_update: BulkUpdateStatusRequest):
    try:
        return await DocumentController.bulk_update_status(bulk_update)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


from bson.errors import InvalidId
from fastapi.responses import StreamingResponse

class AsyncIteratorWrapper:
    def __init__(self, stream):
        self.stream = stream

    async def __aiter__(self):
        while True:
            chunk = await self.stream.read(8192)
            if not chunk:
                break
            yield chunk

@router.get("/download/{file_id}")
async def download_document(
    file_id: str,
    gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
):
    """Download a document from GridFS by file_id"""
    try:
        # Validate ObjectId
        try:
            file_obj_id = PyObjectId(file_id)
        except (InvalidId, ValueError):
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Attempt to get the GridFS file
        try:
            gridfs_file = await gridfs_bucket.open_download_stream(file_obj_id)
        except Exception:
            raise HTTPException(status_code=404, detail="File not found in GridFS")

        # Get metadata and filename
        content_type = gridfs_file.metadata.get("content_type", "application/octet-stream") if gridfs_file.metadata else "application/octet-stream"
        filename = gridfs_file.filename or "document"

        # Ensure correct extension
        extension = mimetypes.guess_extension(content_type) or ""
        if extension and not filename.endswith(extension):
            filename += extension

        return StreamingResponse(
            AsyncIteratorWrapper(gridfs_file),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")


@router.post("/attachment", status_code=status.HTTP_201_CREATED )
async def upload_attachment(
    file: UploadFile = File(...),
    gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
):
    """Upload a file to GridFS"""
    try:
        # Validate file type
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

        # Validate file size
        max_size = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

        # Upload to GridFS
        file_id = await gridfs_bucket.upload_from_stream(
            filename=file.filename,
            source=content,
            metadata={"content_type": file.content_type}
        )

        return {"file_id": str(file_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GridFS upload failed: {str(e)}")