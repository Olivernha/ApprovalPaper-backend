from fastapi import APIRouter, HTTPException, Path, status, Depends
from typing import List
from app.controllers.documentController import DocumentController
from app.schema.document import DocumentCreate, DocumentResponse, DocumentUpdateNormal, DocumentUpdateAdmin
from app.schema.base import PyObjectId
router = APIRouter(
    prefix="/document",
    tags=["document"],
)

@router.get("/", response_model=List[DocumentResponse])
async def get_documents():
    try:
        return await DocumentController.get_documents()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    try:
        return await DocumentController.create_document(document)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{doc_id}", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def update_document_normal(
    update_data: DocumentUpdateNormal,
    doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document"),
):
    try:
        return await DocumentController.update_document(doc_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{doc_id}/admin", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def update_document_admin(
    update_data: DocumentUpdateAdmin,
    doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document")
):
    try:
        return await DocumentController.update_document(doc_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))