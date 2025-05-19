from fastapi import HTTPException, status
from typing import List
from app.schema.base import PyObjectId
from app.schema.department import DepartmentCreate, DepartmentInDB
from app.schema.documentType import DocumentTypeCreate, DocumentTypeInDB
from app.services.departmentService import DepartmentService

class DepartmentController:
    @staticmethod
    async def create_department(department: DepartmentCreate, collection_name: str = "departments") -> DepartmentInDB:
        try:
            service = DepartmentService(collection_name=collection_name)
            return await service.create_department(department)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def add_document_type(department_id: PyObjectId, doc_type: DocumentTypeCreate, collection_name: str = "departments") -> DepartmentInDB:
        try:
            
          #  print(f'Adding document type to department {department_id} with data: {doc_type}')
            service = DepartmentService(collection_name=collection_name)
            return await service.add_document_type(department_id, doc_type)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def get_document_types(department_id: str, collection_name: str = "departments") -> List[DocumentTypeInDB]:
        try:
            service = DepartmentService(collection_name=collection_name)
            return await service.get_document_types(department_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def get_all_document_types_with_departments(collection_name: str = "departments") -> List[DocumentTypeInDB]:
        try:
            service = DepartmentService(collection_name=collection_name)
            return await service.get_all_document_types_with_departments()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))