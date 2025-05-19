from fastapi import APIRouter, Body, HTTPException, Path, Query, status, Depends
from typing import List, Union, Optional
from app.controllers.documentController import DocumentController
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
from app.config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/document",
    tags=["document"],
    responses={404: {"description": "Not found"}},
)

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
    """
    Get paginated list of documents with filtering options
    
    - **page**: Page number (starts from 1)
    - **limit**: Number of documents per page (1-100)
    - **search**: Optional search text (searches title, ref_no, and created_by)
    - **status**: Optional status filter (Not Filed, Filed, Suspended)
    - **department_id**: Optional department ID filter
    - **document_type_id**: Optional document type ID filter
    - **sort_field**: Field to sort by (created_date, title, ref_no, status, etc.)
    - **sort_order**: Sort direction (1 for ascending, -1 for descending)
    """
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
    update_data: Union[DocumentUpdateNormal, DocumentUpdateAdmin],
    doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document")
):
    try:
        return await DocumentController.update_document(doc_id, update_data)
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