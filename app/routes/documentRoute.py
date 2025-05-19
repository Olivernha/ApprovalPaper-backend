from fastapi import APIRouter, Body, HTTPException, Path, status, Depends
from typing import List, Union
from app.controllers.documentController import DocumentController
from app.schema.document import DocumentCreate, DocumentDelete, DocumentResponse, DocumentUpdateNormal, DocumentUpdateAdmin
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
async def update_document(
    update_data: Union[DocumentUpdateNormal, DocumentUpdateAdmin],
    doc_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document")
):
    try:
        print("Updating document with ID:", doc_id, "and data:", update_data)
        return await DocumentController.update_document(doc_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_delete: DocumentDelete,
    document_id: PyObjectId = Path(..., title="Document ID", description="The ObjectId of the document")
) -> dict:
    try:
        return await DocumentController.delete_document(document_id, document_delete.current_user)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
