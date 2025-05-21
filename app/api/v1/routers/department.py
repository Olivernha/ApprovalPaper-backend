from fastapi import APIRouter, Path, status
from typing import List
from app.api.v1.controllers.department import DepartmentController
from app.schemas.base import PyObjectId
from app.schemas.department import DepartmentCreate, DepartmentResponse, DocumentTypeCreate, DocumentTypeInDB, DocumentTypeWithDepartment
from app.core.config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/department",
    tags=["department"],
    responses={404: {"description": "Not found"}},
)
@router.get("/", response_model=List[DepartmentResponse])
async def get_departments():
    return await DepartmentController.get_departments()

@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponse)
async def create_department(department: DepartmentCreate):
    return await DepartmentController.create_department(department)

@router.post("/{department_id}/document-type", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponse)
async def add_document_type(
    department_id: PyObjectId = Path(..., title="Department ID", description="The ObjectId of the department"),
    document_type: DocumentTypeCreate = ...
):
    return await DepartmentController.add_document_type(department_id, document_type)

@router.get("/{department_id}/document-types", response_model=List[DocumentTypeInDB])
async def get_document_types(
    department_id: str = Path(..., title="Department ID", description="The ObjectId of the department")
):
    return await DepartmentController.get_document_types(department_id)

@router.get("/document-types", response_model=List[DocumentTypeWithDepartment])
async def get_all_document_types():
    return await DepartmentController.get_all_document_types_with_departments()