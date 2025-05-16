# from typing import List
# from fastapi import APIRouter, Path, status
#
# from ..schema import DocumentTypeCreate, DocumentTypeInDB
# from ..config import settings
#
# router = APIRouter(
#     prefix=f"{settings.API_V1_PREFIX}/document-type",
#     tags=["document-type"],
#     responses={404: {"description": "Not found"}},
# )
#
# @router.post("/create", status_code=status.HTTP_201_CREATED, response_model=DocumentTypeInDB)
# async def create_document_type(document_type: DocumentTypeCreate):
#     return await DocumentTypeController.create_document_type(document_type)
#
# @router.get("/", response_model=List[DocumentTypeInDB])
# async def get_document_types():
#     return await DocumentTypeController.get_document_types()
#
# @router.get("/with-department", response_model=List[DocumentTypeWithDepartment])
# async def get_document_types_with_department():
#     return await DocumentTypeController.get_document_types_with_department()
#
# @router.get("/by-department/{department_id}", response_model=List[DocumentTypeInDB])
# async def get_document_types_by_department_id(
#     department_id: str = Path(
#         ...,
#         title="Department ID",
#         description="The ObjectId of the department",
#         example="60d5f484f1a2c8b8e4f3c8b8"
#     )
# ):
#     return await DocumentTypeController.get_document_types_by_department_id(department_id)