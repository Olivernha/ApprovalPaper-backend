# from typing import List
# from fastapi import HTTPException, status
# from ..models import DocumentTypeModel
# from ..services import DocumentTypeService
# from ..schema import DocumentTypeCreate, DocumentTypeInDB, DocumentTypeWithDepartment
#
# class DocumentTypeController:
#     @staticmethod
#     async def create_document_type(doc_type: DocumentTypeCreate, collection_name: str = DocumentTypeModel.COLLECTION_NAME) -> DocumentTypeInDB:
#         try:
#             service = DocumentTypeService(collection_name=collection_name)
#             created_doc_type = await service.create_document_type(doc_type)
#             return created_doc_type
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#     @staticmethod
#     async def get_document_types(collection_name: str = DocumentTypeModel.COLLECTION_NAME) -> List[DocumentTypeInDB]:
#         try:
#             service = DocumentTypeService(collection_name=collection_name)
#             return await service.get_document_types()
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#     @staticmethod
#     async def get_document_types_with_department(collection_name: str = DocumentTypeModel.COLLECTION_NAME) -> List[DocumentTypeWithDepartment]:
#         try:
#             service = DocumentTypeService(collection_name=collection_name)
#             return await service.get_document_types_with_department()
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#     @staticmethod
#     async def get_document_types_by_department_id(department_id: str, collection_name: str = DocumentTypeModel.COLLECTION_NAME) -> List[DocumentTypeInDB]:
#         try:
#             service = DocumentTypeService(collection_name=collection_name)
#             return await service.get_document_types_by_department_id(department_id)
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))