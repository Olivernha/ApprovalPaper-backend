from fastapi import APIRouter, File, Path, UploadFile, status
from typing import Dict, List
from app.api.v1.controllers.department import DepartmentController
from app.core.exceptions import handle_service_exception
from app.schemas.base import PyObjectId
from app.schemas.department import DepartmentCreate, DepartmentInDB, DepartmentResponse, DocumentTypeCreate, DocumentTypeInDB, DocumentTypeWithDepartment
from app.core.config import settings
from app.services.department import DepartmentService

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/department",
    tags=["department"],
    responses={404: {"description": "Not found"}},
)

# 1. Specific routes with fixed paths and variables at the end
@router.get("/", response_model=List[DepartmentResponse])
async def get_departments():
    return await DepartmentController.get_departments()

@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponse)
async def create_department(department: DepartmentCreate):
    return await DepartmentController.create_department(department)

@router.get("/document-types", response_model=List[DocumentTypeWithDepartment])
async def get_all_document_types():
    return await DepartmentController.get_all_document_types_with_departments()


@router.get("/name/document-types/{department_name}", response_model=List[DocumentTypeInDB])
async def get_document_types_by_department_name(
    department_name: str = Path(..., title="Department Name", description="The name of the department")
):
    return await DepartmentController.get_document_types_by_department_name(department_name)


@router.get("/{department_id}/document-types", response_model=List[DocumentTypeInDB])
async def get_document_types(
    department_id: str = Path(..., title="Department ID", description="The ObjectId of the department")
):
    return await DepartmentController.get_document_types(department_id)

@router.post("/{department_id}/document-type", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponse)
async def add_document_type(
    department_id: PyObjectId = Path(..., title="Department ID", description="The ObjectId of the department"),
    document_type: DocumentTypeCreate = ...
):
    return await DepartmentController.add_document_type(department_id, document_type)

@router.delete("/{department_id}/document-types/{document_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type(
    department_id: PyObjectId = Path(..., title="Department ID", description="The ObjectId of the department"),
    document_type_id: PyObjectId = Path(..., title="Document Type ID", description="The ObjectId of the document type")
):
    return await DepartmentController.delete_document_type(department_id, document_type_id)


