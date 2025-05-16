from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from app.controllers import DocumentController
from ..schema.document import DocumentCreate, DocumentResponse
# from ..services import  DocumentService

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


@router.post("/", status_code=status.HTTP_201_CREATED , response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    try:
        print("Creating document with data:", document)
        return await DocumentController.create_document(document)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

