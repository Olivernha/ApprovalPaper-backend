from fastapi import HTTPException, status
from bson import ObjectId
from typing import List

from app.core.database import MongoDB
from app.models.department import DepartmentModel
from app.schemas.department import DepartmentCreate, DepartmentInDB, DocumentTypeCreate, DocumentTypeInDB, DepartmentBase, DocumentTypeWithDepartment
from app.services.utils import validate_document_types
from app.core.utils import to_object_id
from app.core.exceptions import handle_service_exception

class DepartmentService:
    def __init__(self, collection_name: str = "departments"):
        self.collection_name = collection_name

    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]

    async def get_all_departments(self) -> List[DepartmentInDB]:

        try:
            departments = await self.get_collection().find().to_list(length=None)
            print(departments)
            return [DepartmentInDB(**dept) for dept in departments]
        except Exception as e:
            handle_service_exception(e)
        
    async def create_department(self, department_data: DepartmentCreate) -> DepartmentInDB:
        try:
            existing_department = await self.get_collection().find_one({"name": department_data.name})
            if existing_department:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name exists")

            validate_document_types(department_data.document_types)

            existing_prefixes = await self.get_collection().aggregate([
                {"$unwind": "$document_types"},
                {"$match": {"document_types.prefix": {"$in": [doc.prefix for doc in department_data.document_types]}}},
                {"$project": {"prefix": "$document_types.prefix"}}
            ]).to_list(length=len(department_data.document_types))
            if existing_prefixes:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document type prefix already exists")

            doc_types_with_ids = [
                {**doc.model_dump(), "_id": ObjectId()} for doc in department_data.document_types
            ]
            department_dict = department_data.model_dump()
            department_dict["document_types"] = doc_types_with_ids

            result = await self.get_collection().insert_one(department_dict)
            department_dict["_id"] = result.inserted_id
            return DepartmentInDB(**department_dict)
        except Exception as e:
            handle_service_exception(e)

    async def add_document_type(self, department_id: str, doc_type: DocumentTypeCreate) -> DepartmentInDB:
        try:
            department_id = to_object_id(department_id)
            department = await self.get_collection().find_one({"_id": department_id})
            if not department:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

            existing_doc_types = department.get("document_types", [])
            validate_document_types([doc_type], existing_doc_types)

            existing_prefixes = await self.get_collection().aggregate([
                {"$unwind": "$document_types"},
                {"$match": {"document_types.prefix": doc_type.prefix}},
                {"$project": {"prefix": "$document_types.prefix"}}
            ]).to_list(length=1)
            if existing_prefixes:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document type prefix already exists")

            doc_type_dict = doc_type.model_dump()
            doc_type_dict["_id"] = ObjectId()
            await self.get_collection().update_one(
                {"_id": department_id},
                {"$push": {"document_types": doc_type_dict}}
            )
            department = await self.get_collection().find_one({"_id": department_id})
            return DepartmentInDB(**department)
        except Exception as e:
            handle_service_exception(e)

    async def get_document_types(self, department_id: str) -> List[DocumentTypeInDB]:
        try:
            department_id = to_object_id(department_id)
            department = await self.get_collection().find_one({"_id": department_id})
            if not department:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
            doc_types = department.get("document_types", [])
            return [DocumentTypeInDB(**dt) for dt in doc_types]
        except Exception as e:
            handle_service_exception(e)

    async def get_all_document_types_with_departments(self) -> List[DocumentTypeWithDepartment]:
        try:
            departments = await self.get_collection().find().to_list(length=None)
            all_doc_types = []
            for dept in departments:
                department = DepartmentBase(**dept)
                doc_types = dept.get("document_types", [])
                for doc_type in doc_types:
                    doc_type_with_dept = DocumentTypeWithDepartment(
                        **doc_type,
                        department=department
                    )
                    all_doc_types.append(doc_type_with_dept)
            return all_doc_types
        except Exception as e:
            handle_service_exception(e)

    async def has_document_type_in_department(self, department_id: str, doc_type_id: str) -> bool:
        try:
            department_id = to_object_id(department_id)
            doc_type_id = to_object_id(doc_type_id)
            department = await self.get_collection().find_one({"_id": department_id})
            if not department:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
            doc_types = department.get("document_types", [])
            return any(dt["_id"] == doc_type_id for dt in doc_types)
        except Exception as e:
            handle_service_exception(e)

    @staticmethod
    async def ensure_indexes() -> None:
        try:
            await DepartmentModel.ensure_indexes()
        except Exception as e:
            handle_service_exception(e)