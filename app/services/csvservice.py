from datetime import datetime
import io
import pandas as pd
from typing import Any, List, Dict, Coroutine
from bson import ObjectId
from fastapi import HTTPException, UploadFile, status
from pymongo import UpdateOne, ReplaceOne

from app.core.database import MongoDB
from app.core.exceptions import handle_service_exception
from app.schemas.admin import AdminUser
from app.schemas.base import PyObjectId
from app.schemas.department import csvDepartment
from app.schemas.document import csvDocumentData
from app.services.department import DepartmentService


class CSVImportService:
    """
    Service for importing data from CSV files into MongoDB.
    This optimized version uses bulk database operations to significantly
    improve performance for large datasets.
    """
    @staticmethod
    def _convert_oids(data: Any) -> Any:
        """Recursively converts MongoDB ObjectIds and datetimes to strings for JSON serialization."""
        if isinstance(data, list):
            return [CSVImportService._convert_oids(i) for i in data]
        if isinstance(data, dict):
            return {k: CSVImportService._convert_oids(v) for k, v in data.items()}
        if isinstance(data, ObjectId):
            return str(data)
        if isinstance(data, datetime):
            return data.isoformat()
        return data

    def get_department_collection(self):
        """Returns the 'departments' collection from MongoDB."""
        return MongoDB.get_database()["departments"]

    def get_admin_collection(self):
        """Returns the 'admins' collection from MongoDB."""
        return MongoDB.get_database()["admins"]

    def get_document_collection(self):
        """Returns the 'documents' collection from MongoDB."""
        return MongoDB.get_database()["documents"]

    async def import_csv(self, department_file: UploadFile, document_type_file: UploadFile, generated_id_file: UploadFile) -> List[Dict]:
        """
        Imports and processes department, document type, and generated ID data from CSV files.
        It uses a bulk update operation to efficiently save data to MongoDB.
        """
        try:
            # 1. Validate and Read CSV files
            for file in [department_file, document_type_file, generated_id_file]:
                if not file.filename.endswith('.csv'):
                    raise HTTPException(status_code=400, detail=f"File {file.filename} must be a CSV file")

            departments_df = pd.read_csv(io.BytesIO(await department_file.read()))
            document_types_df = pd.read_csv(io.BytesIO(await document_type_file.read()))
            generated_ids_df = pd.read_csv(io.BytesIO(await generated_id_file.read()))

            # 2. Clean column names
            for df in [departments_df, document_types_df, generated_ids_df]:
                df.columns = df.columns.str.strip()

            # 3. Process Data in Memory
            dept_lookup = {row['id']: row['name'] for _, row in departments_df.iterrows()}
            prefix_lookup = self._build_prefix_lookup(generated_ids_df)
            dept_doc_types = self._build_dept_doc_types(document_types_df, dept_lookup, prefix_lookup)

            if not dept_doc_types:
                 raise HTTPException(status_code=400, detail="No valid departments or document types found in CSVs.")

            # 4. Prepare Bulk Database Operations
            print("Preparing bulk update for departments...")
            bulk_operations = []
            department_ids_to_fetch = []

            existing_depts_cursor = self.get_department_collection().find(
                {"inserted_id": {"$in": list(dept_doc_types.keys())}},
                {"_id": 1, "inserted_id": 1, "document_types": 1}
            )
            existing_depts = {dept['inserted_id']: dept async for dept in existing_depts_cursor}


            for dept_id, doc_types in dept_doc_types.items():
                dept_name = dept_lookup.get(dept_id)
                if not dept_name:
                    continue

                department_dict = {

                    'inserted_id': dept_id,
                    'name': dept_name,
                    'status': 1,
                    'created_date': datetime.now(),
                    'document_types': doc_types
                }

                existing_dept = existing_depts.get(dept_id)
                if existing_dept:
                    # Logic to merge document types for existing departments
                    existing_doc_types_map = {doc['inserted_id']: doc for doc in existing_dept.get('document_types', [])}
                    for new_doc_type in department_dict['document_types']:
                        doc_type_inserted_id = new_doc_type['inserted_id']
                        if doc_type_inserted_id in existing_doc_types_map:
                            new_doc_type['_id'] = existing_doc_types_map[doc_type_inserted_id]['_id']
                        else:
                            new_doc_type['_id'] = ObjectId()
                    
                    updated_doc_types = list(existing_doc_types_map.values())
                    for new_doc in department_dict['document_types']:
                        if new_doc['inserted_id'] not in existing_doc_types_map:
                            updated_doc_types.append(new_doc)
                    
                    department_dict['document_types'] = updated_doc_types
                    department_dict['_id'] = existing_dept['_id']
                else:
                    # Assign new ObjectIds for new departments and their doc types
                    department_dict['_id'] = ObjectId()
                    for doc_type in department_dict['document_types']:
                        doc_type['_id'] = ObjectId()

                bulk_operations.append(ReplaceOne(
                    {"inserted_id": dept_id},
                    department_dict,
                    upsert=True
                ))
                department_ids_to_fetch.append(dept_id)

            # 5. Execute Bulk Write
            if bulk_operations:
                print(f"Executing bulk write for {len(bulk_operations)} departments...")
                await self.get_department_collection().bulk_write(bulk_operations)
                print("Bulk write complete.")

                # 6. Fetch updated documents and convert for response
                final_depts_cursor = self.get_department_collection().find(
                    {"inserted_id": {"$in": department_ids_to_fetch}}
                )
                departments = [self._convert_oids(dept) async for dept in final_depts_cursor]
                print(f"Successfully processed {len(departments)} departments")
                return departments
            else:
                 raise HTTPException(
                    status_code=400,
                    detail="No departments could be processed. Please check your CSV files."
                )

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in import_csv: {str(e)}")
            handle_service_exception(e)
        return []

    def _build_prefix_lookup(self, generated_ids_df: pd.DataFrame) -> dict:
        """Helper to build a lookup dictionary for prefix information."""
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
            prefix_lookup[doc_type_id]['counters'][year] = int(gen_row['number'])
        return prefix_lookup

    def _build_dept_doc_types(self, document_types_df: pd.DataFrame, dept_lookup: dict, prefix_lookup: dict) -> dict:
        """Helper to build the nested document type structure for departments."""
        dept_doc_types = {}
        for _, doc_type_row in document_types_df.iterrows():
            dept_id = doc_type_row['departmentid']
            doc_type_id = doc_type_row['id']

            if dept_id not in dept_lookup:
                continue

            if dept_id not in dept_doc_types:
                dept_doc_types[dept_id] = []

            prefix_info = prefix_lookup.get(doc_type_id)
            doc_type = {
                '_id': ObjectId(),
                'inserted_id': doc_type_id,
                'name': doc_type_row['name'],
                'prefix': prefix_info['prefix'] if prefix_info else f"DEFAULT_{doc_type_id}",
                'padding': prefix_info['padding'] if prefix_info else 4,
                'counters': prefix_info['counters'] if prefix_info else {},
                'created_date': datetime.now()
            }
            dept_doc_types[dept_id].append(doc_type)
        return dept_doc_types

    async def import_documents_from_csv(self, approval_paper_file: UploadFile) -> list[Any] | dict[str, int | str]:
        """
        Imports a large number of documents from a single CSV file.
        Uses chunked processing and batch inserts for high performance.
        """
        if not approval_paper_file.filename.endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

        try:
            # Define required columns to reduce memory usage
            required_columns = ["id", "RefNo", "Title", "StatusID", "CreatedBy", "CreatedDate",
                                "FiledBy", "FiledDate", "DocumentTypeID", "DepartmentID"]

            # Initialize response list
            inserted_doc_ids = []
            chunk_size = 50000

            # Process CSV in chunks
            for chunk in pd.read_csv(
                    io.BytesIO(await approval_paper_file.read()),
                    usecols=required_columns,
                    chunksize=chunk_size,
                    on_bad_lines='skip'
            ):
                # Clean column names
                chunk.columns = chunk.columns.str.strip()

                # Get unique IDs for departments and document types
             
                all_dept_ids = [int(d) for d in chunk["DepartmentID"].dropna().unique() if str(d).isdigit()]
                all_doc_type_ids = [int(d) for d in chunk["DocumentTypeID"].dropna().unique() if str(d).isdigit()]
                

                # Fetch department and document type mappings
                dept_map = await DepartmentService().get_department_map_by_custom_ids(all_dept_ids)
                doc_type_map = await DepartmentService().get_document_type_map_by_custom_ids(all_doc_type_ids)
                
                if not dept_map or not doc_type_map:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No valid departments or document types found in the provided CSV. Please import departments or document types first."
                    )

                # Vectorized validation and data transformation
                chunk = chunk.dropna(subset=["id", "RefNo", "Title", "StatusID", "CreatedBy", "CreatedDate",
                                            "DocumentTypeID", "DepartmentID"])
                chunk["CreatedDate"] = pd.to_datetime(chunk["CreatedDate"], errors='coerce')
                chunk["FiledDate"] = pd.to_datetime(chunk["FiledDate"], errors='coerce')
                chunk = chunk[chunk["CreatedDate"].notna()]  # Drop rows with invalid CreatedDate

                # Map status IDs to strings
                status_map = {1: 'Not Filed', 2: 'Filed', 3: 'Suspended'}
                chunk["Status"] = chunk["StatusID"].map(status_map).fillna('Suspended')

                # Map department and document type IDs
                chunk["DepartmentMongoID"] = chunk["DepartmentID"].map(dept_map)
                chunk["DocumentTypeMongoID"] = chunk["DocumentTypeID"].map(doc_type_map)

                # Filter out rows with invalid mappings
                chunk = chunk[chunk["DepartmentMongoID"].notna() & chunk["DocumentTypeMongoID"].notna()]

                # Skip rows with empty titles
                empty_title_count = len(chunk[chunk["Title"].str.strip().str.len() == 0])
                chunk = chunk[chunk["Title"].str.strip().str.len() > 0]
                if empty_title_count > 0:
                    print(f"Skipped {empty_title_count} rows with empty titles in this chunk.")

                if chunk.empty:
                    print("Skipping chunk: No valid documents after mapping and title validation.")
                    continue

                # Prepare documents for insertion
                documents_to_insert = [
                    {
                        "_id": ObjectId(),
                        "ref_no": str(row["RefNo"]).strip(),
                        "title": str(row["Title"]).strip(),
                        "status": row["Status"],
                        "created_by": str(row["CreatedBy"]).strip(),
                        "created_date": row["CreatedDate"],
                        "filed_by": str(row["FiledBy"]).strip() if pd.notna(row["FiledBy"]) else None,
                        "filed_date": row["FiledDate"] if pd.notna(row["FiledDate"]) else None,
                        "document_type_id": row["DocumentTypeMongoID"],
                        "department_id": row["DepartmentMongoID"]
                    }
                    for _, row in chunk.iterrows()  # Fallback to iterrows for final transformation
                ]

                if documents_to_insert:
                    print(f"Inserting {len(documents_to_insert)} documents in chunk...")
                    result = await self.get_document_collection().insert_many(documents_to_insert, ordered=False)
                    inserted_doc_ids.extend(result.inserted_ids)
                    print(f"Inserted {len(result.inserted_ids)} documents in chunk.")

            print(f"Successfully processed {len(inserted_doc_ids)} documents")
            return {"inserted_count": len(inserted_doc_ids), "status": "success"}

        except Exception as e:
            print(f"An error occurred during document import: {e}")
            handle_service_exception(e)
            return []

    def _is_valid_row(self, row: pd.Series) -> bool:
        """Helper to validate a row from the document CSV."""
        return all(pd.notna(row.get(col)) for col in ["id", "RefNo", "Title", "StatusID", "CreatedBy", "CreatedDate", "DocumentTypeID", "DepartmentID"])


    async def import_admins_from_csv(self, admin_file: UploadFile) -> List[dict]:
        """
        Imports admins from a CSV file using bulk operations to
        handle creations and updates efficiently.
        """
        if not admin_file.filename.endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")
        
        try:
            admin_df = pd.read_csv(io.BytesIO(await admin_file.read()))
            admin_df.columns = admin_df.columns.str.strip()
            
            usernames_from_csv = [
                name.strip() for name in admin_df["username"].dropna().unique() if isinstance(name, str) and name.strip()
            ]

            if not usernames_from_csv:
                raise HTTPException(status_code=400, detail="No valid usernames found in CSV.")

            existing_admins_cursor = self.get_admin_collection().find(
                {"username": {"$in": usernames_from_csv}},
                {"username": 1, "_id": 1}
            )
            existing_admins = {admin["username"] async for admin in existing_admins_cursor}

            bulk_operations = []
            
            for username in usernames_from_csv:
                if username not in existing_admins:
                    admin_doc = AdminUser(username=username).model_dump(by_alias=True)
                    admin_doc["_id"] = ObjectId()
                    bulk_operations.append(ReplaceOne(
                        {"username": username},
                        admin_doc,
                        upsert=True
                    ))
            
            if bulk_operations:
                print(f"Executing bulk write for {len(bulk_operations)} new admins...")
                await self.get_admin_collection().bulk_write(bulk_operations, ordered=False)
                print("Admin import complete.")

            final_admins_cursor = self.get_admin_collection().find({"username": {"$in": usernames_from_csv}})
            admins = [{
                "_id": str(admin["_id"]),
                "username": admin["username"]
            } async for admin in final_admins_cursor]

            print(f"Successfully processed {len(admins)} admins")
            return admins

        except Exception as e:
            print(f"An error occurred during admin import: {e}")
            handle_service_exception(e)
            
        return []
