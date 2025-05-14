from typing import List
from fastapi import APIRouter

from app.controllers import DocumentTypeController
from app.schema import DocumentTypeCreate , DocumentTypeWithDepartment

router= APIRouter(
    prefix="/documentType",
    tags=["documentType"],
)

@router.post("/create", status_code=201)
async def create_documentType(document_type: DocumentTypeCreate):
    return await DocumentTypeController.create_document_type(document_type)


@router.get("/", status_code=200)
async def get_documentType():
    return await DocumentTypeController.get_document_types()

@router.get("/with-department", response_model=List[DocumentTypeWithDepartment])
async def get_document_types_with_department():
    return await DocumentTypeController.get_document_types_with_department(collection_name="document_types")