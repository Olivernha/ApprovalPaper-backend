from fastapi import HTTPException , status
from app.schema import DepartmentCreate
from app.schema.department import Department
from app.services import DepartmentService


class DepartmentController:
    @staticmethod
    async def create_department(department : DepartmentCreate , collection_name: str = "users") -> Department:
        try:
            service = DepartmentService(collection_name=collection_name)
            created_department = await service.create_department(department)
            return created_department
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
           