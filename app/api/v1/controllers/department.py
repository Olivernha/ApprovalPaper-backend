from typing import List
from app.schemas.base import PyObjectId
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
    async def get_active_departments() -> List[DepartmentInDB]:
        return await DepartmentService().get_active_departments()
        
    @staticmethod
    async def create_department(department: DepartmentCreate) -> DepartmentInDB:
        return await DepartmentService().create_department(department)

    @staticmethod
    async def update_departments_status(departments: List[str], status: int) -> List[DepartmentInDB]:
        return await DepartmentService().update_departments_status(departments, status)
    
    @staticmethod
    async def delete_document_type(department_id: PyObjectId, document_type_id: PyObjectId) -> None:
        await DepartmentService().delete_document_type(department_id, document_type_id)

    @staticmethod
    async def delete_document_type_by_name(department_name: str, document_type_id: PyObjectId) -> None:
        await DepartmentService().delete_document_type_by_name(department_name, document_type_id)

    @staticmethod
    async def add_document_type(department_id: PyObjectId, document_type: DocumentTypeCreate) -> DepartmentInDB:
        return await DepartmentService().add_document_type(department_id, document_type)

    @staticmethod
    async def add_document_type_by_name(department_name: str, document_type: DocumentTypeCreate) -> DepartmentInDB:
        return await DepartmentService().add_document_type_by_name(department_name, document_type)

    @staticmethod
    async def get_document_types(department_id: PyObjectId) -> List[DocumentTypeInDB]:
        return await DepartmentService().get_document_types(department_id)

    @staticmethod
    async def get_document_types_by_department_name(department_name: str) -> List[DocumentTypeInDB]:
        return await DepartmentService().get_document_types_by_department_name(department_name)

    @staticmethod
    async def get_all_document_types_with_departments() -> List[DocumentTypeWithDepartment]:
        return await DepartmentService().get_all_document_types_with_departments()

    @staticmethod
    async def delete_department_by_id(department_id: PyObjectId) -> None:
        await DepartmentService().delete_department_by_id(department_id)

    @staticmethod
    async def delete_department_by_name(department_name: str) -> None:
        return await DepartmentService().delete_department_by_name(department_name)