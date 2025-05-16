# from typing import Dict, Any, List
# from bson import ObjectId
#
# from ..database import MongoDB
# from ..schema import DocumentTypeInDB
#
#
# class DocumentTypeModel:
#     """Model for document types in MongoDB"""
#     COLLECTION_NAME = "document_types"
#
#     @staticmethod
#     async def to_document_type(doc_data: Dict[str, Any]) -> DocumentTypeInDB:
#         """Convert document data from MongoDB to DocumentTypeInDB model"""
#         # Convert ObjectId to string for proper serialization
#         if "_id" in doc_data and isinstance(doc_data["_id"], ObjectId):
#             doc_data["_id"] = str(doc_data["_id"])
#
#         # Convert department_id to string if it's an ObjectId
#         if "department_id" in doc_data and isinstance(doc_data["department_id"], ObjectId):
#             doc_data["department_id"] = str(doc_data["department_id"])
#
#         return DocumentTypeInDB(**doc_data)
#
#     @staticmethod
#     async def to_document_type_with_department(doc_data: Dict[str, Any]) -> DocumentTypeWithDepartment:
#         """Convert document data with department info to DocumentTypeWithDepartment model"""
#         # Process department data first if available
#         department_data = None
#         if "department" in doc_data and doc_data["department"]:
#             # Usually the lookup returns department as a list with one item
#             department = doc_data["department"][0] if isinstance(doc_data["department"], list) else doc_data["department"]
#
#             # Convert department ObjectId to string
#             if "_id" in department and isinstance(department["_id"], ObjectId):
#                 department["_id"] = str(department["_id"])
#
#             department_data = department
#
#         # Remove department list and replace with processed department
#         if "department" in doc_data:
#             doc_data.pop("department")
#
#         # Convert document ObjectIds to strings
#         if "_id" in doc_data and isinstance(doc_data["_id"], ObjectId):
#             doc_data["_id"] = str(doc_data["_id"])
#
#         if "department_id" in doc_data and isinstance(doc_data["department_id"], ObjectId):
#             doc_data["department_id"] = str(doc_data["department_id"])
#
#         # Create the document type with department
#         doc_type = DocumentTypeWithDepartment(**doc_data, department=department_data)
#         return doc_type
#
#     @staticmethod
#     async def ensure_indexes() -> None:
#         """Create indexes for document_types collection"""
#         db = MongoDB.get_database()
#         await db[DocumentTypeModel.COLLECTION_NAME].create_index("name", unique=True)
#         await db[DocumentTypeModel.COLLECTION_NAME].create_index("prefix", unique=True)
#         await db[DocumentTypeModel.COLLECTION_NAME].create_index("department_id")