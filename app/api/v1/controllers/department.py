from typing import List
from app.services.department import DepartmentService
from app.schemas.department import DepartmentCreate, DepartmentInDB, DocumentTypeCreate, DocumentTypeInDB, DocumentTypeWithDepartment
from app.core.exceptions import handle_service_exception

class DepartmentController:
    @staticmethod
    async def get_departments() -> List[DepartmentInDB]:
        try:
            return await DepartmentService().get_all_departments()
        except Exception as e:
            handle_service_exception(e)
    @staticmethod
    async def create_department(department: DepartmentCreate) -> DepartmentInDB:
        return await DepartmentService().create_department(department)

    @staticmethod
    async def add_document_type(department_id: str, document_type: DocumentTypeCreate) -> DepartmentInDB:
        return await DepartmentService().add_document_type(department_id, document_type)

    @staticmethod
    async def get_document_types(department_id: str) -> List[DocumentTypeInDB]:
        return await DepartmentService().get_document_types(department_id)

    @staticmethod
    async def get_all_document_types_with_departments() -> List[DocumentTypeWithDepartment]:
        return await DepartmentService().get_all_document_types_with_departments()