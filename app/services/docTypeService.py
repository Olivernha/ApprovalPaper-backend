# from typing import List
# from fastapi import HTTPException, status
# from bson import ObjectId
# from ..database import MongoDB
# from ..schema import DocumentTypeCreate, DocumentTypeInDB
# from ..models import DocumentTypeModel
#
# class DocumentTypeService:
#     def __init__(self, collection_name: str = DocumentTypeModel.COLLECTION_NAME):
#         self.collection_name = collection_name
#
#     def get_collection(self):
#         return MongoDB.get_database()[self.collection_name]
#
#     async def get_document_types(self) -> List[DocumentTypeInDB]:
#         """Retrieve all document types from the database"""
#         try:
#             results = self.get_collection().find()
#             documents = await results.to_list(length=100)
#             return [await DocumentTypeModel.to_document_type(doc) for doc in documents]
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#
#     async def create_document_type(self, doc_type: DocumentTypeCreate) -> DocumentTypeInDB:
#             """Create a new document type"""
#             db = MongoDB.get_database()
#             if not await db["departments"].find_one({"_id": ObjectId(doc_type.department_id)}):
#                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department_id")
#
#             existing = await self.get_collection().find_one({"name": doc_type.name})
#             if existing:
#                 raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document type name exists")
#             existing = await self.get_collection().find_one({"prefix": doc_type.prefix})
#             if existing:
#                 raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prefix exists")
#
#             doc_type_data = doc_type.model_dump()
#             result = await self.get_collection().insert_one(doc_type_data)
#             return await DocumentTypeModel.to_document_type({"_id": result.inserted_id, **doc_type_data})
#     async def get_document_types_with_department(self) -> List[DocumentTypeWithDepartment]:
#             """Retrieve all document types with their department details"""
#             try:
#                 pipeline = [
#                     {
#                         "$lookup": {
#                             "from": "departments",
#                             "localField": "department_id",
#                             "foreignField": "_id",
#                             "as": "department"
#                         }
#                     },
#                     {
#                         "$match": {
#                             "department": {"$ne": []}  # Exclude document types with no matching department
#                         }
#                     }
#                 ]
#                 results = self.get_collection().aggregate(pipeline)
#                 documents = await results.to_list(length=100)
#                 return [await DocumentTypeModel.to_document_type_with_department(doc) for doc in documents]
#             except Exception as e:
#                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#     async def get_document_types_by_department_id(self, department_id: str) -> List[DocumentTypeInDB]:
#         try:
#             pipeline = [
#                 {
#                     "$match": {
#                         "department_id": ObjectId(department_id)
#                     }
#                 }
#             ]
#             results = self.get_collection().aggregate(pipeline)
#             documents = await results.to_list(length=100)
#             return [await DocumentTypeModel.to_document_type(doc) for doc in documents]
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#     @staticmethod
#     async def ensure_indexes() -> None:
#         """Ensure indexes for the document_types collection"""
#         await DocumentTypeModel.ensure_indexes()