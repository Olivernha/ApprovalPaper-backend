# import re
# from fastapi import APIRouter, FastAPI, HTTPException, UploadFile, File
# from pydantic import BaseModel
# from typing import List, Dict, Optional, Union
# from datetime import datetime
# import pandas as pd
# import io
# from bson import ObjectId
# from pymongo import MongoClient

# import pandas as pd 
# from app.core.config import settings
# from app.core.exceptions import handle_service_exception
# from app.schemas.base import PyObjectId
# from app.schemas.department import DepartmentCreate, DocumentTypeCreate
# from app.schemas.document import DocumentCreate, DocumentResponse

# # MongoDB client setup
# client = MongoClient(settings.MONGODB_URL)
# db = client[settings.DATABASE_NAME]

# def get_departments_collection():
#     return db["departments"]

# def get_documents_collection():
#     return db["documents"]


# router = APIRouter(
#     prefix=f"{settings.API_V1_PREFIX}/dataTransfer",
#     tags=["dataTransfer"],
#     responses={404: {"description": "Not found"}},
# )
# def parse_csv(file_content: bytes, filename: str) -> List[Dict]:
#     df = pd.read_csv(io.BytesIO(file_content))
#     df = df.replace({pd.NA: None}).fillna(None)
#     return df.to_dict('records')

# def extract_prefix_and_year(ref_no: str) -> tuple[Optional[str], Optional[str]]:
#     match = re.match(r"([A-Z/]+)\d*/(\d{2,4})", ref_no)
#     if match:
#         return match.group(1), match.group(2)
#     return None, None

# def parse_date(date_str: Union[str, None]) -> Optional[datetime]:
#     """
#     Parses a date string into a datetime object. Returns None if parsing fails.
#     """
#     try:
#         return datetime.strptime(date_str, "%Y-%m-%d") if date_str else None
#     except ValueError:
#         return None

# async def generate_ref_no(db, document_type_id: str, year: str) -> str:
#     doc_type = await db.document_types.find_one({"id": document_type_id})
#     if not doc_type:
#         raise HTTPException(status_code=404, detail=f"Document type ID {document_type_id} not found")
    
#     prefix = doc_type.get("name", "").replace(" ", "_").upper()[:10]
#     counters = doc_type.get("counters", {})
#     counter = counters.get(year, 0) + 1
#     ref_no = f"{prefix}/{str(counter).zfill(2)}/{year}"
    
#     # Update counter in document type
#     await db.document_types.update_one(
#         {"id": document_type_id},
#         {"$set": {f"counters.{year}": counter}},
#         upsert=True
#     )
#     return ref_no


# @router.post("/csv-to-mongodb", status_code=200)
# async def import_all_data(
#     department_file: UploadFile = File(...),
#     document_type_file: UploadFile = File(...),
#     generated_id_file: UploadFile = File(...),
#     approval_paper_file: UploadFile = File(...)
# ):
#     try:
#         # Validate file extensions
#         for file in [department_file, document_type_file, generated_id_file, approval_paper_file]:
#             if not file.filename.endswith('.csv'):
#                 raise HTTPException(status_code=400, detail=f"File {file.filename} must be a CSV file")

#         # Read uploaded CSV files
#         departments_df = pd.read_csv(io.BytesIO(await department_file.read()))
#         document_types_df = pd.read_csv(io.BytesIO(await document_type_file.read()))
#         generated_ids_df = pd.read_csv(io.BytesIO(await generated_id_file.read()))
#         approval_paper_df = pd.read_csv(io.BytesIO(await approval_paper_file.read()))

#         # Create mappings for validation
#         department_ids = set(departments_df['id'])
#         document_type_ids = set(document_types_df['id'])

#         # Validate generatedid.csv
#         for _, row in generated_ids_df.iterrows():
#             if row['departmentid'] not in department_ids:
#                 raise HTTPException(status_code=400, detail=f"Invalid departmentid {row['departmentid']} in generatedid.csv")
#             if row['documenttypeid'] not in document_type_ids:
#                 raise HTTPException(status_code=400, detail=f"Invalid documenttypeid {row['documenttypeid']} in generatedid.csv")

#         # Create mapping of document type ID to prefix, padding, and counters from generatedid.csv
#         doc_type_info = {}
#         for _, row in generated_ids_df.iterrows():
#             doc_type_id = row['documenttypeid']
#             doc_type_info[doc_type_id] = {
#                 'prefix': row['prefix'],
#                 'padding': int(row['padding']),
#                 'counters': {str(int(row['year'])): int(row['number'])},
#                 'departmentid': row['departmentid']
#             }

#         # Group document types by department (based on generatedid.csv)
#         department_groups = generated_ids_df.groupby('departmentid')

#         for dept_id, group in department_groups:
#             # Get department details
#             dept_row = departments_df[departments_df['id'] == dept_id]
#             if dept_row.empty:
#                 continue  # Skip if department not found

#             dept_name = dept_row['name'].iloc[0]
            
#             # Create document types
#             document_types = []
#             for _, row in group.iterrows():
#                 doc_type_id = row['documenttypeid']
#                 doc_type_row = document_types_df[document_types_df['id'] == doc_type_id]
#                 if doc_type_row.empty:
#                     continue  # Skip if document type not found

#                 doc_info = doc_type_info[doc_type_id]
#                 document_types.append(DocumentTypeCreate(
#                     custom_id=doc_type_id,  # Store original CSV ID
#                     name=doc_type_row['name'].iloc[0],
#                     prefix=doc_info['prefix'],
#                     padding=doc_info['padding'],
#                     counters=doc_info['counters'],
#                     created_date=datetime.now()
#                 ))

#             # Create department
#             department = DepartmentCreate(
#                 custom_id=dept_id,  # Store original CSV ID
#                 name=dept_name,
#                 created_date=datetime.now(),
#                 document_types=document_types
#             )

#             # Convert to MongoDB-compatible format
#             department_dict = department.model_dump(by_alias=True)
#             department_dict['_id'] = PyObjectId(ObjectId())  # MongoDB unique ID
            
#             # Check if department already exists by custom_id
#             existing_dept = await get_departments_collection().find_one({{"name": dept_name}})
#             if existing_dept:
#                 # Merge document types, updating existing ones and adding new ones
#                 existing_doc_types = {doc['custom_id']: doc for doc in existing_dept.get('document_types', [])}
#                 new_doc_types = department_dict['document_types']
                
#                 for new_doc_type in new_doc_types:
#                     new_doc_type['_id'] = PyObjectId(ObjectId())  # Assign new PyObjectId
#                     existing_doc_types[new_doc_type['custom_id']] = new_doc_type  # Update or add by custom_id

#                 department_dict['document_types'] = list(existing_doc_types.values())
#                 department_dict['_id'] = existing_dept['_id']  # Use existing _id
#             else:
#                 # Assign PyObjectId to each document type
#                 for doc_type in department_dict['document_types']:
#                     doc_type['_id'] = PyObjectId(ObjectId())

#             # Insert or update into MongoDB
#             await get_departments_collection().update_one(
#                 {"custom_id": dept_id},
#                 {"$set": department_dict},
#                 upsert=True
#             )

#         # Load all departments and their document types from MongoDB for validation
#         department_cursor = await get_departments_collection().find().to_list(length=None)
#         valid_dept_ids = set()
#         valid_doc_type_ids = set()
#         dept_doc_type_map = {}  # Maps document_type_id to its valid department_id

#         for dept in department_cursor:
#             dept_id = dept.get('custom_id')  # Use custom_id from CSV
#             valid_dept_ids.add(dept_id)
#             for doc_type in dept.get('document_types', []):
#                 doc_type_id = doc_type.get('custom_id')  # Use custom_id from CSV
#                 valid_doc_type_ids.add(doc_type_id)
#                 dept_doc_type_map[doc_type_id] = dept_id

#         documents = []
#         for _, row in approval_paper_df.iterrows():
#             # Handle potential missing or invalid values
#             created_date = datetime.strptime(row["CreatedDate"], "%Y-%m-%d") if isinstance(row["CreatedDate"], str) else None
#             if created_date is None:
#                 raise HTTPException(status_code=400, detail=f"Invalid CreatedDate in row {row['id']}")

#             filed_date = None
#             if isinstance(row["FiledDate"], str) and row["FiledDate"].strip():
#                 filed_date = parse_date(row["FiledDate"])
#                 if filed_date is None:
#                     raise HTTPException(status_code=400, detail=f"Invalid FiledDate in row {row['id']}")

#             # Clean and validate fields
#             ref_no = row["RefNo"].strip() if isinstance(row["RefNo"], str) else ""
#             title = row["Title"].strip() if isinstance(row["Title"], str) else ""
#             created_by = row["CreatedBy"].strip() if isinstance(row["CreatedBy"], str) else ""
#             filed_by = row["FiledBy"].strip() if isinstance(row["FiledBy"], str) and row["FiledBy"].strip() else None
#             status_id = int(row["StatusID"]) if pd.notna(row["StatusID"]) and str(row["StatusID"]).isdigit() else None
#             document_type_id = int(row["DocumentTypeID"]) if pd.notna(row["DocumentTypeID"]) and str(row["DocumentTypeID"]).isdigit() else None
#             department_id = int(row["DepartmentID"]) if pd.notna(row["DepartmentID"]) and str(row["DepartmentID"]).isdigit() else None

#             if not ref_no or not title or not created_by or status_id is None or document_type_id is None or department_id is None:
#                 raise HTTPException(status_code=400, detail=f"Missing or invalid required fields in row {row['id']}")

#             # Validate department_id and document_type_id against MongoDB data
#             if department_id not in valid_dept_ids:
#                 raise HTTPException(status_code=400, detail=f"Invalid department_id {department_id} in row {row['id']}")
#             if document_type_id not in valid_doc_type_ids:
#                 raise HTTPException(status_code=400, detail=f"Invalid document_type_id {document_type_id} in row {row['id']}")
#             if dept_doc_type_map.get(document_type_id) != department_id:
#                 raise HTTPException(status_code=400, detail=f"Document type {document_type_id} does not belong to department {department_id} in row {row['id']}")

#             # Create document
#             document = DocumentCreate(
#                 ref_no=ref_no,
#                 title=title,
#                 status_id=status_id,
#                 created_by=created_by,
#                 created_date=created_date,
#                 filed_by=filed_by,
#                 filed_date=filed_date,
#                 document_type_id=document_type_id,
#                 department_id=department_id
#             )

#             # Convert to MongoDB-compatible format
#             document_dict = document.model_dump(by_alias=True)
#             document_dict["_id"] = PyObjectId(ObjectId())

#             # Insert into MongoDB
#             await get_documents_collection().insert_one(document_dict)
            
#             # Retrieve inserted document
#             inserted_doc = await get_documents_collection().find_one({"_id": document_dict["_id"]})
#             documents.append(DocumentResponse(**inserted_doc))

#         return documents

#     except Exception as e:
#         handle_service_exception(e)