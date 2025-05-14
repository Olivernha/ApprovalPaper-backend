from fastapi import APIRouter

from app.controllers import DocumentTypeController
from app.schema import DocumentTypeCreate

router= APIRouter(
    prefix="/documentType",
    tags=["documentType"],
)

@router.post("/create", status_code=201)
async def create_documentType(document_type: DocumentTypeCreate):
    return await DocumentTypeController.create_document_type(document_type)
