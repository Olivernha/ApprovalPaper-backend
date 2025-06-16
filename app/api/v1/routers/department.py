from bson import ObjectId
from fastapi import APIRouter, Path, status, HTTPException
from typing import List
from app.api.v1.controllers.department import DepartmentController
from app.core.exceptions import handle_service_exception
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

@router.get("/document-types", response_model=List[DocumentTypeWithDepartment])
async def get_all_document_types():
    return await DepartmentController.get_all_document_types_with_departments()

@router.get("/name/document-types/{department_name}", response_model=List[DocumentTypeInDB])
async def get_document_types_by_department_name(
    department_name: str = Path(..., title="Department Name", description="The name of the department")
):
    return await DepartmentController.get_document_types_by_department_name(department_name)

@router.get("/{department}/document-types", response_model=List[DocumentTypeInDB])
async def get_document_types(
    department: str = Path(..., title="Department ID or Name", description="The ObjectId or name of the department")
):
    if ObjectId.is_valid(department):
        return await DepartmentController.get_document_types(department)
    else:
        return await DepartmentController.get_document_types_by_department_name(department)

@router.post("/{department}/document-type", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponse)
async def add_document_type(
    department: str = Path(..., title="Department ID or Name", description="The ObjectId or name of the department"),
    document_type: DocumentTypeCreate = ...
):
    if ObjectId.is_valid(department):
        return await DepartmentController.add_document_type(PyObjectId(department), document_type)
    else:
        return await DepartmentController.add_document_type_by_name(department, document_type)

@router.delete("/{department}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department: str = Path(..., title="Department ID or Name", description="The ObjectId or name of the department")
):
    if ObjectId.is_valid(department):
        await DepartmentController.delete_department_by_id(PyObjectId(department))
    else:
        await DepartmentController.delete_department_by_name(department)

@router.delete("/{department}/document-types/{document_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type(
    department: str = Path(..., title="Department ID or Name", description="The ObjectId or name of the department"),
    document_type_id: PyObjectId = Path(..., title="Document Type ID", description="The ObjectId of the document type")
):
    if ObjectId.is_valid(department):
        return await DepartmentController.delete_document_type(PyObjectId(department), document_type_id)
    else:
        return await DepartmentController.delete_document_type_by_name(department, document_type_id)