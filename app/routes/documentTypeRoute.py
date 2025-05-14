from fastapi import APIRouter

from app.schema.documentType import DocumentType
from app.controllers import DocumentTypeController

router= APIRouter(
    prefix="/documentType",
    tags=["documentType"],
)

@router.post("/create", status_code=201)
async def create_documentType(document_type: DocumentType):
    return await DocumentTypeController.create_document_type(document_type)
