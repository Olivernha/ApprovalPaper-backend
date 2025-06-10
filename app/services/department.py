from datetime import datetime
import io
from turtle import pd
import uuid
from fastapi import HTTPException, status
from bson import ObjectId
from typing import Dict, List, Optional, Any, Coroutine


from app.core.database import MongoDB
from app.models.department import DepartmentModel
from app.schemas.base import PyObjectId
from app.schemas.department import DepartmentCreate, DepartmentInDB, DepartmentInDBMinimal, DepartmentResponse, DocumentTypeCreate, DocumentTypeInDB,  DocumentTypeWithDepartment, csvDepartment, csvDocumentType
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
                {**doc.model_dump(), "_id": ObjectId() , "created_date": datetime.now()} for doc in department_data.document_types
            ]
            department_dict = department_data.model_dump()
            department_dict["document_types"] = doc_types_with_ids

            department_dict["created_date"] = datetime.now()

            result = await self.get_collection().insert_one(department_dict)
            department_dict["_id"] = result.inserted_id
            return DepartmentInDB(**department_dict)
        except Exception as e:
            handle_service_exception(e)
    from fastapi import HTTPException, status

    async def delete_document_type(self, department_id: str, document_type_id: str) -> dict:
        try:
            department_oid = to_object_id(department_id)
            document_type_oid = to_object_id(document_type_id)
            
            department = await self.get_collection().find_one({"_id": department_oid})
            if not department:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
            
            if document_type_oid not in [doc["_id"] for doc in department.get("document_types", [])]:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document type not found")
            
            await self.get_collection().update_one(
                {"_id": department_oid},
                {"$pull": {"document_types": {"_id": document_type_oid}}}
            )
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
            doc_type_dict["created_date"] = datetime.now()
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


    async def get_document_types_by_department_name(self, department_name: str) -> List[DocumentTypeInDB]:
        try:
            department = await self.get_collection().find_one({"name": department_name.upper()})
        
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
                department = DepartmentInDBMinimal(**dept)
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


    async def get_document_types_by_custom_id(self, custom_id: int) -> ObjectId | None:
        try:
            result = await self.get_collection().find_one(
                {"document_types.inserted_id": custom_id},
                {"document_types.$": 1}
            )
            if result and result.get("document_types"):
                return result["document_types"][0]["_id"]
            return None
        except Exception as e:
            handle_service_exception(e)

    async def get_department_by_custom_id(self, department_id: int):
        try:
            department = await self.get_collection().find_one({"inserted_id": department_id})
            return department["_id"] if department else None
        except Exception as e:
            handle_service_exception(e)

    async def get_department_map_by_custom_ids(self, custom_ids: List[int]) -> Dict[int, PyObjectId]:
        """
        Efficiently fetches a map of custom department IDs to MongoDB ObjectIds.
        
        Args:
            custom_ids: A list of integer IDs (e.g., from the CSV).
            
        Returns:
            A dictionary mapping each custom ID to its corresponding MongoDB _id.
            Example: {101: ObjectId('...'), 102: ObjectId('...')}
        """
        if not custom_ids:
            return {}
        
        dept_map = {}
        cursor = self.get_collection().find(
            {"inserted_id": {"$in": custom_ids}},
            {"_id": 1, "inserted_id": 1}
        )
        async for dept in cursor:
            dept_map[dept["inserted_id"]] = dept["_id"]
        
        return dept_map
    
    async def get_document_type_map_by_custom_ids(self, custom_ids: List[int]) -> Dict[int, PyObjectId]:
        """
        Efficiently fetches a map of custom document type IDs to their MongoDB ObjectIds.
        Uses an aggregation pipeline to search within the embedded document_types array.

        Args:
            custom_ids: A list of integer IDs for document types.

        Returns:
            A dictionary mapping each custom document type ID to its MongoDB _id.
            Example: {201: ObjectId('...'), 202: ObjectId('...')}
        """
        if not custom_ids:
            return {}
            
        pipeline = [
            {"$unwind": "$document_types"},
            {"$match": {"document_types.inserted_id": {"$in": custom_ids}}},
            {"$project": {
                "_id": 0,
                "doc_type_id": "$document_types.inserted_id",
                "mongo_id": "$document_types._id"
            }}
        ]
        
        doc_type_map = {}
        cursor = self.get_collection().aggregate(pipeline)
        async for doc in cursor:
            doc_type_map[doc["doc_type_id"]] = doc["mongo_id"]
            
        return doc_type_map