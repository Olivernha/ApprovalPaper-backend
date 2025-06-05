
from datetime import datetime
import io
import pandas as pd
from typing import Any, List
from bson import ObjectId
from fastapi import HTTPException, UploadFile ,status

from app.core.database import MongoDB
from app.core.exceptions import handle_service_exception
from app.schemas.admin import AdminUser
from app.schemas.base import PyObjectId
from app.schemas.department import csvDepartment
from app.schemas.document import csvDocumentData
from app.services.department import DepartmentService


class CSVImportService:

    def get_department_collection(self):
        return MongoDB.get_database()["departments"]

    def get_admin_collection(self):
        return MongoDB.get_database()["admins"]  

    def get_document_collection(self):
        return MongoDB.get_database()["documents"] 
    async def import_csv(self, department_file: UploadFile, document_type_file: UploadFile, generated_id_file: UploadFile) -> list[csvDepartment] | None:
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
                        updated_count += 1
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
                existing_dept = await self.get_department_collection().find_one({"inserted_id": dept_id})

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
                await self.get_department_collection().update_one(
                    {"inserted_id": dept_id},
                    {"$set": department_dict},
                    upsert=True
                )

                # Retrieve the inserted/updated document for response
                inserted_dept = await self.get_department_collection().find_one({"inserted_id": dept_id})
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

    async def import_documents_from_csv(self, approval_paper_file: UploadFile) -> List[csvDocumentData]:
        if not approval_paper_file.filename.endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

        approval_paper_df = pd.read_csv(io.BytesIO(await approval_paper_file.read()))
        documents = []

        for _, row in approval_paper_df.iterrows():
            try:
                # Validate and parse created_date
                created_date = None
                if isinstance(row["CreatedDate"], str) and row["CreatedDate"].strip():
                    try:
                        created_date = datetime.strptime(row["CreatedDate"], "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        continue  # Skip row with invalid CreatedDate
                else:
                    continue  # Skip row with missing CreatedDate

                # Validate and parse filed_date
                filed_date = None
                if isinstance(row["FiledDate"], str) and row["FiledDate"].strip():
                    try:
                        filed_date = datetime.strptime(row["FiledDate"], "%Y-%m-%d %H:%M:%S.%f")
                    except (ValueError, TypeError):
                        continue  # Skip row with invalid FiledDate

                # Clean and validate fields
                ref_no = row["RefNo"].strip() if isinstance(row["RefNo"], str) else ""
                title = row["Title"].strip() if isinstance(row["Title"], str) else ""
                created_by = row["CreatedBy"].strip() if isinstance(row["CreatedBy"], str) else ""
                filed_by = row["FiledBy"].strip() if isinstance(row["FiledBy"], str) and row[
                    "FiledBy"].strip() else None
                status_id = int(row["StatusID"]) if pd.notna(row["StatusID"]) and str(
                    row["StatusID"]).isdigit() else None
                document_type_id = int(row["DocumentTypeID"]) if pd.notna(row["DocumentTypeID"]) and str(
                    row["DocumentTypeID"]).isdigit() else None
                department_id = int(row["DepartmentID"]) if pd.notna(row["DepartmentID"]) and str(
                    row["DepartmentID"]).isdigit() else None

                # Skip if any required field is invalid
                if not ref_no or not title or not created_by or status_id is None or document_type_id is None or department_id is None:
                    continue

                dept_id = await DepartmentService().get_department_by_custom_id(department_id)
                doc_type_id = await DepartmentService().get_document_types_by_custom_id(document_type_id)

                document = csvDocumentData(
                    inserted_id=row["id"],
                    ref_no=ref_no,
                    title=title,
                    status='Not Filed' if status_id == 1 else 'Filed' if status_id == 2 else 'Suspended',
                    created_by=created_by,
                    created_date=created_date,
                    filed_by=filed_by,
                    filed_date=filed_date,
                    document_type_id=PyObjectId(doc_type_id),
                    department_id=PyObjectId(dept_id)
                )

                document_dict = document.model_dump(by_alias=True)
                document_dict["_id"] = PyObjectId(ObjectId())

                await self.get_document_collection().insert_one(document_dict)
                inserted_doc = await self.get_document_collection().find_one({"_id": document_dict["_id"]})
                documents.append(csvDocumentData(**inserted_doc))

            except Exception:
                # Silently skip row on any unexpected error (or add logging if needed)
                continue

        return documents
    
    async def import_admins_from_csv(self, admin_file: UploadFile) -> List[AdminUser]:
        if not admin_file.filename.endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

        admin_df = pd.read_csv(io.BytesIO(await admin_file.read()))
        admins = []

        # Clean column names
        admin_df.columns = admin_df.columns.str.strip()

        for _, row in admin_df.iterrows():
            try:
                # Clean and validate fields
                username = row["username"].strip() if isinstance(row["username"], str) and row["username"].strip() else None

                # Skip if any required field is invalid
                if  not username:
                    continue

                # Create admin object
                admin = AdminUser(
                    username=username
                )

                admin_dict = admin.model_dump(by_alias=True)
                admin_dict["_id"] = PyObjectId(ObjectId())

                # Check if admin already exists
                existing_admin = await self.get_admin_collection().find_one({"username": username})
                if existing_admin:
                    print(f"Updating existing admin: {username}")
                    admin_dict["_id"] = existing_admin["_id"]
                    await self.get_admin_collection().update_one(
                        {"username": username},
                        {"$set": admin_dict},
                        upsert=True
                    )
                else:
                    print(f"Creating new admin: {username}")
                    await self.get_admin_collection().insert_one(admin_dict)

                # Retrieve the inserted/updated admin for response
                inserted_admin = await self.get_admin_collection().find_one({"_id": admin_dict["_id"]})
                if inserted_admin:
                    admins.append(AdminUser(**inserted_admin))

            except Exception:
                # Silently skip row on any unexpected error
                continue

        if not admins:
            raise HTTPException(
                status_code=400,
                detail="No admins could be processed. Please check your CSV file."
            )

        print(f"Successfully processed {len(admins)} admins")
        return admins