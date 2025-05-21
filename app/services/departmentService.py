from fastapi import HTTPException, status
from bson import ObjectId
from typing import List
from app.database import MongoDB
from app.models.departmentModel import DepartmentModel
from app.schema.department import DepartmentCreate, DepartmentInDB, DocumentTypeCreate, DocumentTypeInDB, DepartmentBase, DocumentTypeWithDepartment

class DepartmentService:
    def __init__(self, collection_name: str = "departments"):
        self.collection_name = collection_name

    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]

    async def create_department(self, department_data: DepartmentCreate) -> DepartmentInDB:
        """Create a new department with embedded document types"""
        existing_department = await self.get_collection().find_one({"name": department_data.name})
        if existing_department:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name exists")

        # Validate unique document type names and prefixes
        doc_type_names = {doc.name for doc in department_data.document_types}
        doc_type_prefixes = {doc.prefix for doc in department_data.document_types}
        if len(doc_type_names) != len(department_data.document_types):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate document type names")
        if len(doc_type_prefixes) != len(department_data.document_types):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate document type prefixes")

        # Assign ObjectId to each document type
        doc_types_with_ids = []
        for doc_type in department_data.document_types:
            doc_type_dict = doc_type.model_dump()
            doc_type_dict["_id"] = ObjectId()
            doc_types_with_ids.append(doc_type_dict)

        # Convert department to dict and embed modified document types
        department_dict = department_data.model_dump()
        department_dict["document_types"] = doc_types_with_ids

        result = await self.get_collection().insert_one(department_dict)
        department_dict["_id"] = result.inserted_id

        return DepartmentInDB(**department_dict)

    async def add_document_type(self, department_id: str, doc_type: DocumentTypeCreate) -> DepartmentInDB:
        """Add a document type to an existing department"""
        department = await self.get_collection().find_one({"_id": ObjectId(department_id)})
      
        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        # Check for duplicate name or prefix
        existing_doc_types = department.get("document_types", [])
        if any(dt["name"] == doc_type.name for dt in existing_doc_types):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document type name exists")
        if any(dt["prefix"] == doc_type.prefix for dt in existing_doc_types):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document type prefix exists")

        doc_type_dict = doc_type.model_dump()
        doc_type_dict["_id"] = ObjectId()
        await self.get_collection().update_one(
            {"_id": ObjectId(department_id)},
            {"$push": {"document_types": doc_type_dict}}
        )
        department = await self.get_collection().find_one({"_id": ObjectId(department_id)})
        return DepartmentInDB(**department)

    async def get_document_types(self, department_id: str) -> List[DocumentTypeInDB]:
        """Retrieve document types for a department"""
        department = await self.get_collection().find_one({"_id": ObjectId(department_id)})
        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        
        doc_types = department.get("document_types", [])
        return [DocumentTypeInDB(**dt) for dt in doc_types]

    async def get_all_document_types_with_departments(self) -> List[DocumentTypeWithDepartment]:
       try:
            departments = await self.get_collection().find().to_list()
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
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    


    async def has_document_type_in_deptartment(self, department_id: str, doc_type_id: str) -> bool:
        """Check if a document type exists in a department"""
        department = await self.get_collection().find_one({"_id": ObjectId(department_id)})
        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        doc_types = department.get("document_types", [])
        return any(dt["_id"] == ObjectId(doc_type_id) for dt in doc_types)
    
    @staticmethod
    async def ensure_indexes() -> None:
        """Ensure indexes for the department collection"""
        try:
            await DepartmentModel.ensure_indexes()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        