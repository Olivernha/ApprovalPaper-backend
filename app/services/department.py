from datetime import datetime
import io
import uuid
from fastapi import HTTPException, status
from bson import ObjectId
from typing import Dict, List, Optional, Any, Coroutine

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

    async def import_csv(self, department_file, document_type_file, generated_id_file) -> list[Any] | None:
        try:
            # Validate file extensions
            for file in [department_file, document_type_file, generated_id_file]:
                if not file.filename.endswith('.csv'):
                    raise HTTPException(status_code=400, detail=f"File {file.filename} must be a CSV file")

            # Read uploaded CSV files
            departments_df = pd.read_csv(io.BytesIO(await department_file.read()))
            document_types_df = pd.read_csv(io.BytesIO(await document_type_file.read()))
            generated_ids_df = pd.read_csv(io.BytesIO(await generated_id_file.read()))

            # Clean column names (strip whitespace)
            departments_df.columns = departments_df.columns.str.strip()
            document_types_df.columns = document_types_df.columns.str.strip()
            generated_ids_df.columns = generated_ids_df.columns.str.strip()

            # STEP 1: Connect Document Types to Departments
            print("Step 1: Connecting document types to departments...")

            # Create department lookup
            dept_lookup = {row['id']: row['name'] for _, row in departments_df.iterrows()}

            # Group document types by department
            dept_doc_types = {}
            for _, doc_type_row in document_types_df.iterrows():
                dept_id = doc_type_row['departmentid']
                doc_type_id = doc_type_row['id']
                doc_type_name = doc_type_row['name']

                if dept_id not in dept_lookup:
                    print(f"Warning: Department ID {dept_id} not found for document type {doc_type_name}")
                    continue

                if dept_id not in dept_doc_types:
                    dept_doc_types[dept_id] = []

                # Create basic document type (without prefix info yet)
                doc_type = {
                    'inserted_id': doc_type_id,
                    'name': doc_type_name,
                    'prefix': None,  # Will be filled in Step 2
                    'padding': None,  # Will be filled in Step 2
                    'counters': {},  # Will be filled in Step 2
                    'created_date': datetime.now()
                }
                dept_doc_types[dept_id].append(doc_type)

            print(
                f"Connected {sum(len(docs) for docs in dept_doc_types.values())} document types to {len(dept_doc_types)} departments")

            # STEP 2: Add prefix information from generatedid.csv
            print("Step 2: Adding prefix information from generatedid.csv...")

            # Create lookup for prefix information by document type ID
            prefix_lookup = {}
            for _, gen_row in generated_ids_df.iterrows():
                doc_type_id = gen_row['documenttypeid']
                year = str(int(gen_row['year']))

                if doc_type_id not in prefix_lookup:
                    prefix_lookup[doc_type_id] = {
                        'prefix': gen_row['prefix'],
                        'padding': int(gen_row['padding']),
                        'counters': {},
                    }

                # Add counter for this year
                prefix_lookup[doc_type_id]['counters'][year] = int(gen_row['number'])


            # Update document types with prefix information
            updated_count = 0
            for dept_id, doc_types in dept_doc_types.items():
                for doc_type in doc_types:
                    doc_type_id = doc_type['inserted_id']

                    if doc_type_id in prefix_lookup:
                        # Use actual prefix info
                        prefix_info = prefix_lookup[doc_type_id]
                        doc_type['prefix'] = prefix_info['prefix']
                        doc_type['padding'] = prefix_info['padding']
                        doc_type['counters'] = prefix_info['counters']

                    else:
                        # Use default values for document types without prefix info
                        doc_type['prefix'] = f"DEFAULT_{doc_type_id}"
                        doc_type['padding'] = 4
                        doc_type['counters'] = {}



            print(f"Updated {updated_count} document types with prefix information")

            # STEP 3: Create and save departments with embedded document types
            print("Step 3: Saving departments to MongoDB...")

            departments = []
            for dept_id, doc_types in dept_doc_types.items():
                dept_name = dept_lookup[dept_id]

                # Create department with embedded document types
                department_dict = {
                    'inserted_id': dept_id,
                    'name': dept_name,
                    'created_date': datetime.now(),
                    'document_types': doc_types
                }

                # Check if department already exists
                existing_dept = await self.get_collection().find_one({"inserted_id": dept_id})

                if existing_dept:
                    print(f"Updating existing department: {dept_name}")

                    # Merge document types - preserve existing _ids
                    existing_doc_types = {doc['inserted_id']: doc for doc in existing_dept.get('document_types', [])}

                    for new_doc_type in department_dict['document_types']:
                        doc_type_id = new_doc_type['inserted_id']

                        if doc_type_id in existing_doc_types:
                            # Update existing document type but preserve its MongoDB _id
                            existing_doc_type = existing_doc_types[doc_type_id]
                            new_doc_type['_id'] = existing_doc_type['_id']
                            existing_doc_types[doc_type_id] = new_doc_type
                        else:
                            # Add new document type with new _id
                            new_doc_type['_id'] = PyObjectId(ObjectId())
                            existing_doc_types[doc_type_id] = new_doc_type

                    department_dict['document_types'] = list(existing_doc_types.values())
                    department_dict['_id'] = existing_dept['_id']  # Preserve existing MongoDB _id
                else:
                    print(f"Creating new department: {dept_name}")

                    # New department - assign MongoDB _ids
                    department_dict['_id'] = PyObjectId(ObjectId())
                    for doc_type in department_dict['document_types']:
                        doc_type['_id'] = PyObjectId(ObjectId())

                # Insert or update department in MongoDB
                await self.get_collection().update_one(
                    {"inserted_id": dept_id},
                    {"$set": department_dict},
                    upsert=True
                )

                # Retrieve the inserted/updated document for response
                inserted_dept = await self.get_collection().find_one({"inserted_id": dept_id})
                if inserted_dept:
                    departments.append(csvDepartment(**inserted_dept))

            print(f"Successfully processed {len(departments)} departments")

            if not departments:
                raise HTTPException(
                    status_code=400,
                    detail="No departments could be processed. Please check your CSV files."
                )

            return departments

        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            print(f"Error in import_csv: {str(e)}")
            handle_service_exception(e)

    from bson import ObjectId

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