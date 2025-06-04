from datetime import datetime
import io
import uuid
from fastapi import HTTPException, status
from bson import ObjectId
from typing import Dict, List, Optional

import pandas as pd

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

    async def import_csv(self, department_file, document_type_file, generated_id_file) -> DepartmentResponse:

        try:
                # Validate file extensions
                for file in [department_file, document_type_file, generated_id_file]:
                    if not file.filename.endswith('.csv'):
                        raise HTTPException(status_code=400, detail=f"File {file.filename} must be a CSV file")

                # Read uploaded CSV files
                departments_df = pd.read_csv(io.BytesIO(await department_file.read()))
                document_types_df = pd.read_csv(io.BytesIO(await document_type_file.read()))
                generated_ids_df = pd.read_csv(io.BytesIO(await generated_id_file.read()))

                # Create mappings for validation
                department_ids = set(departments_df['id'])
                document_type_ids = set(document_types_df['id'])

                # Validate generatedid.csv
                for _, row in generated_ids_df.iterrows():
                    if row['departmentid'] not in department_ids:
                        raise HTTPException(status_code=400, detail=f"Invalid departmentid {row['departmentid']} in generatedid.csv")
                    if row['documenttypeid'] not in document_type_ids:
                        raise HTTPException(status_code=400, detail=f"Invalid documenttypeid {row['documenttypeid']} in generatedid.csv")

                # Create a mapping of document type ID to prefix, padding, and counters from generatedid.csv
                doc_type_info = {}
                for _, row in generated_ids_df.iterrows():
                    doc_type_id = row['documenttypeid']
                    doc_type_info[doc_type_id] = {
                        'prefix': row['prefix'],
                        'padding': int(row['padding']),
                        'counters': {str(int(row['year'])): int(row['number'])},
                        'departmentid': row['departmentid'],
                        'inserted_id': row['id'] 
                    }

                # Group document types by department (based on generatedid.csv)
                departments = []
                department_groups = generated_ids_df.groupby('departmentid')

                for dept_id, group in department_groups:
                    # Get department details
                    dept_row = departments_df[departments_df['id'] == dept_id]
                    if dept_row.empty:
                        continue  # Skip if department not found

                    dept_name = dept_row['name'].iloc[0]
                    
                    # Create document types
                    document_types = []
                    for _, row in group.iterrows():
                        doc_type_id = row['documenttypeid']
                        doc_type_row = document_types_df[document_types_df['id'] == doc_type_id]
                        if doc_type_row.empty:
                            continue  # Skip if document type not found

                        doc_info = doc_type_info[doc_type_id]
                        document_types.append(csvDocumentType(
                            inserted_id=doc_info['inserted_id'],
                            name=doc_type_row['name'].iloc[0],
                            prefix=doc_info['prefix'],
                            padding=doc_info['padding'],
                            counters=doc_info['counters'],
                            created_date=datetime.now()
                        ))

                    # Create department
                    department = csvDepartment(
                        inserted_id=dept_id,
                        name=dept_name,
                        created_date=datetime.now(),
                        document_types=document_types
                    )

                    # Convert to MongoDB-compatible format
                    department_dict = department.model_dump(by_alias=True)

                    # Check if department already exists
                    existing_dept = await self.get_collection().find_one({"name": dept_name})
                    if existing_dept:
                        # Merge document types, updating existing ones and adding new ones
                        existing_doc_types = {doc['name']: doc for doc in existing_dept.get('document_types', [])}
                        new_doc_types = department_dict['document_types']
                        
                        for new_doc_type in new_doc_types:
                            new_doc_type['_id'] = PyObjectId(ObjectId())  # Assign new PyObjectId
                            existing_doc_types[new_doc_type['name']] = new_doc_type  # Update or add

                        department_dict['document_types'] = list(existing_doc_types.values())
                        department_dict['_id'] = existing_dept['_id']  # Use existing _id
                    else:
                        # Assign new PyObjectId for new department
                        department_dict['_id'] = PyObjectId(ObjectId())
                        # Assign PyObjectId to each document type
                        for doc_type in department_dict['document_types']:
                            doc_type['_id'] = PyObjectId(ObjectId())

                    # Insert or update into MongoDB
                    await self.get_collection().update_one(
                        {"name": dept_name},
                        {"$set": department_dict},
                        upsert=True
                    )
                    
                    # Retrieve inserted/updated document
                    inserted_dept = await self.get_collection().find_one({"name": dept_name})
                    departments.append(csvDepartment(**inserted_dept))

                return departments

        except Exception as e:
            handle_service_exception(e)

    async def get_document_types_by_custom_id(self, custom_id: int) :
        try:
            document_type = await self.get_collection().find_one({"inserted_id": custom_id})
            # get objectid
            return document_type["_id"] if document_type else None
        except Exception as e:
            handle_service_exception(e)

    async def get_department_by_custom_id(self, department_id: int):
        try:

            department = await self.get_collection().find_one({"inserted_id": department_id})
            return department["_id"] if department else None
        except Exception as e:
            handle_service_exception(e)