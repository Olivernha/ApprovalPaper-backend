
import mimetypes
from bson import ObjectId
from fastapi import APIRouter, Path, Query, Form, File, UploadFile, Depends, HTTPException, status
from typing import List, Optional
from fastapi.responses import StreamingResponse
from typing import Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket

from app.api.v1.controllers.document import DocumentController
from app.core.database import MongoDB
from app.core.dependencies.auth import get_current_user_from_header
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
from app.core.config import settings
from app.core.utils import upload_file_to_gridfs


router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/document",
    tags=["document"],
    responses={404: {"description": "Not found"}},
)


from app.core.config import settings
async def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    db = MongoDB.get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not established")
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name=settings.GRIDFS_BUCKET_NAME)
    return bucket

@router.get("/", response_model=List[DocumentResponse])
async def get_documents():
    return await DocumentController.get_documents()

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
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str = Path(..., title="Document ID", description="The ObjectId of the document")):
    return await DocumentController.get_document_by_id(document_id)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def create_document(document: DocumentCreate, current_user: AuthInAdminDB = Depends(get_current_user_from_header)):
    return await DocumentController.create_document(document, current_user)

@router.put("/{doc_id}", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def update_document(
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
        current_user_data: AuthInAdminDB = Depends(get_current_user_from_header),
        gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
):
    is_admin = current_user_data.is_admin
    if is_admin:
        update_data = DocumentUpdateAdmin(
            doc_id=doc_id,
            title=title,
            document_type_id=document_type_id,
            department_id=department_id,
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
            document_type_id=document_type_id,
            department_id=department_id,
        )
    if file:
        update_data.file_id = await upload_file_to_gridfs(file, gridfs_bucket, current_user_data.username)

    return await DocumentController.update_document(update_data, current_user_data)

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
        document_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document"),
        current_user: AuthInAdminDB = Depends(get_current_user_from_header)
) -> dict:
    return await DocumentController.delete_document(document_id, current_user)

@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_documents(bulk_delete: BulkDeleteRequest, current_user_data: AuthInAdminDB = Depends(get_current_user_from_header)):
    return await DocumentController.bulk_delete_documents(bulk_delete, current_user_data)

@router.post("/bulk-update-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(bulk_update: BulkUpdateStatusRequest, current_user_data: AuthInAdminDB = Depends(get_current_user_from_header)):
    return await DocumentController.bulk_update_status(bulk_update, current_user_data)

class AsyncIteratorWrapper:
    def __init__(self, stream):
        self.stream = stream

    async def __aiter__(self):
        while True:
            chunk = await self.stream.read(8192)
            if not chunk:
                break
            yield chunk

# @router.get("/download/{file_id}")
# async def download_document(
#     file_id: str,
#     gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
# ) -> StreamingResponse:
#     """Download a document from GridFS by file_id"""
#     try:
#         # Validate ObjectId
#         file_obj_id = PyObjectId(file_id)

#         # Attempt to get the GridFS file
#         gridfs_file = await gridfs_bucket.open_download_stream(file_obj_id)

#         # Get metadata and filename
#         content_type = gridfs_file.metadata.get("content_type", "application/octet-stream")
#         filename = gridfs_file.filename or "document"

#         # Ensure correct extension
#         extension = mimetypes.guess_extension(content_type) or ""
#         if extension and not filename.endswith(extension):
#             filename += extension

#         return StreamingResponse(
#             AsyncIteratorWrapper(gridfs_file),
#             media_type=content_type,
#             headers={
#                 "Content-Disposition": f'attachment; filename="{filename}"'
#             }
#         )
#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")



@router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    current_user_data: AuthInAdminDB = Depends(get_current_user_from_header),
   gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
) -> StreamingResponse:
   print('Docuemnt ID'+ document_id)
   return await DocumentController.download_document(document_id, current_user_data, gridfs_bucket)