from datetime import datetime
import io
import mimetypes
from typing import List, Union, Dict, Any, Optional

from bson.errors import InvalidId
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
import pandas as pd
from app.core.utils import AsyncIteratorWrapper 
from app.core.config import settings  # Import settings from the appropriate module

from app.core.database import MongoDB
from app.models.document import DocumentModel
from app.schemas.admin import AuthInAdminDB
from app.schemas.base import PyObjectId
from app.schemas.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentInDB,
    DocumentUpdateNormal,
    DocumentUpdateAdmin,
    DocumentPaginationResponse, csvDocumentData,
)
from app.core.utils import to_object_id
from app.core.exceptions import handle_service_exception
from app.services.admin import AdminService
import logging

from app.services.department import DepartmentService


logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, collection_name: str = DocumentModel.COLLECTION_NAME):
        self.collection_name = collection_name
        self.gridfs_bucket = AsyncIOMotorGridFSBucket(MongoDB.get_database())

    def get_collection(self):
        collection = MongoDB.get_database()[self.collection_name]
        return collection
    def get_file_collection(self, collection_name: str):
        return MongoDB.get_database()[f"{collection_name}"]

    async def get_document_by_id(self, document_id: str) -> DocumentInDB:
        try:
            document = await self.get_collection().find_one({"_id": to_object_id(document_id)})
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            return DocumentInDB(**document)
        except Exception as e:
            handle_service_exception(e)

    async def get_document_by_name(self, document_title: str) -> DocumentInDB:
        try:
            document = await self.get_collection().find_one({"title": {"$regex": document_title, "$options": "i"}})
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            return DocumentInDB(**document)
        except Exception as e:
            handle_service_exception(e)
    async def create_document(self, document: DocumentCreate) -> DocumentInDB:
        try:
           

            # Convert to ObjectId
            document.department_id = to_object_id(document.department_id)
            document.document_type_id = to_object_id(document.document_type_id)

            # Fetch department with matching document_type
            department = await DepartmentService().get_collection().find_one({
                "_id": document.department_id,
                "document_types._id": document.document_type_id
            })
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid department_id or document_type_id"
                )

            year = datetime.now().year
            year_key = str(year)

            # Build update path for atomic increment
            update_result = await DepartmentService().get_collection().update_one(
                {
                    "_id": document.department_id,
                    "document_types._id": document.document_type_id
                },
                {
                    "$inc": {
                        f"document_types.$.counters.{year_key}": 1
                    }
                }
            )
            if update_result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to increment document counter"
                )

            # Retrieve updated document type
            pipeline = [
                {"$match": {"_id": document.department_id}},
                {"$unwind": "$document_types"},
                {"$match": {"document_types._id": document.document_type_id}},
                {"$project": {
                    "prefix": "$document_types.prefix",
                    "padding": "$document_types.padding",
                    "counters": "$document_types.counters"
                }}
            ]
            cursor = DepartmentService().get_collection().aggregate(pipeline)
            doc_type_info = await cursor.to_list(length=1)
            if not doc_type_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document type not found"
                )
            doc_type = doc_type_info[0]
            counter_value = doc_type["counters"].get(year_key, 1)
            padding = doc_type.get("padding", 2)
            prefix = doc_type["prefix"]

            seq_str = str(counter_value)
            padded_seq = seq_str if len(seq_str) > padding else seq_str.zfill(padding)

            year_suffix = str(year % 100)
            ref_no = f"{prefix}/{year_suffix}/{padded_seq}"

            # Ensure ref_no is unique
            existing = await self.get_collection().find_one({"ref_no": ref_no})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Reference number already exists"
                )

            # Prepare final document
            document_data = document.model_dump()
            document_data.update({
                "_id": ObjectId(),
                "ref_no": ref_no,
                "created_date": datetime.now(),
                "status": "Not Filed",
                "created_by": document.created_by,
            })

            # Remove empty fields
            document_data = {k: v for k, v in document_data.items() if v is not None}

            # Insert document
            result = await self.get_collection().insert_one(document_data)
            document_data["_id"] = result.inserted_id

            return DocumentInDB(**document_data)

        except Exception as e:
            handle_service_exception(e)


    async def update_document(
        self,
        update_data: Union[DocumentUpdateNormal, DocumentUpdateAdmin],
        current_user_data: AuthInAdminDB
    ) -> DocumentInDB:
        try:

            document_id = to_object_id(update_data.doc_id)
            username = current_user_data.username
            full_name = current_user_data.full_name
            is_admin = current_user_data.is_admin

            document = await self.get_collection().find_one({"_id": document_id})
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

            if not is_admin and not await self.is_your_document(document_id, full_name):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to update this document")

            if update_data.file_id is not None:
                try:
                    update_data.file_id = PyObjectId(update_data.file_id)
                except InvalidId:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file_id format")

            update_fields = update_data.model_dump(exclude_unset=True, exclude_none=True)
            update_fields.pop("doc_id", None)
            # if fields are empty, remove them from update_fields
            update_fields = {k: v for k, v in update_fields.items() if v is not None}

            if is_admin and isinstance(update_data, DocumentUpdateAdmin):
                if update_fields.get("status") == "Filed":
                    update_fields["filed_by"] = username or document.get("filed_by")
                    update_fields["filed_date"] = datetime.now() or document.get("filed_date")
                elif update_fields.get("status") == "Not Filed":
                    update_fields["filed_by"] = None
                    update_fields["filed_date"] = None
                else:
                    update_fields["filed_by"] = username
            else:
                if not isinstance(update_data, DocumentUpdateNormal):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin fields not allowed for normal users")
                allowed_fields = {"title", "document_type_id", "department_id", "file_id"}
                if any(field not in allowed_fields for field in update_fields):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Normal users can only update title, document_type_id, department_id, and file_id")

            if "file_id" in update_fields and update_fields["file_id"] != document.get("file_id"):
                if document.get("file_id"):
                    for attempt in range(3):
                        try:
                            await self.gridfs_bucket.delete(to_object_id(document["file_id"]))
                            break
                        except Exception as e:
                            logger.warning(f"Attempt {attempt+1} failed to delete GridFS file {document['file_id']}: {str(e)}")
                            if attempt == 2:
                                logger.error(f"Failed to delete GridFS file {document['file_id']} after retries")

            if "document_type_id" in update_fields or "department_id" in update_fields:
                dept_id = to_object_id(update_fields.get("department_id", document["department_id"]))
                doc_type_id = to_object_id(update_fields.get("document_type_id", document["document_type_id"]))
                dept_check = await MongoDB.get_database()["departments"].find_one({
                    "_id": dept_id,
                    "document_types._id": doc_type_id
                })
                if not dept_check:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department_id or document_type_id")

            if "document_type_id" in update_fields:
                update_fields["document_type_id"] = to_object_id(update_fields["document_type_id"])
            if "department_id" in update_fields:
                update_fields["department_id"] = to_object_id(update_fields["department_id"])

            updated_document = await self.get_collection().find_one_and_update(
                {"_id": document_id},
                {"$set": update_fields},
                return_document=True
            )

            if not updated_document:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Update failed or no changes made")

            return DocumentInDB(**updated_document)
        except Exception as e:
            handle_service_exception(e)

    async def get_documents(self) -> List[DocumentInDB]:
        try:
            results = self.get_collection().find()
            documents = await results.to_list()
            return [DocumentInDB(**doc) for doc in documents]
        except Exception as e:
            handle_service_exception(e)

    async def get_documents_paginated(
            self,
            page: int = 1,
            limit: int = 10,
            search: Optional[str] = None,
            status_filter: Optional[str] = None,
            department_id: Optional[str] = None,
            document_type_id: Optional[str] = None,
            sort_field: str = "created_date",
            sort_order: int = -1
    ) -> DocumentPaginationResponse:
        try:
            skip = (page - 1) * limit
            query_filter: Dict[str, Any] = {}

            if search:
                query_filter["$or"] = [
                    {"title": {"$regex": search, "$options": "i"}},
                    {"ref_no": {"$regex": search, "$options": "i"}},
                    {"created_by": {"$regex": search, "$options": "i"}}
                ]

            if status_filter:
                valid_statuses = {"Not Filed", "Filed", "Suspended"}
                if status_filter not in valid_statuses:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of {valid_statuses}")
                query_filter["status"] = status_filter

            if department_id:
                query_filter["department_id"] = to_object_id(department_id)

            if document_type_id:
                query_filter["document_type_id"] = to_object_id(document_type_id)

            valid_sort_fields = {
                "created_date", "title", "ref_no", "status",
                "created_by", "filed_date", "filed_by"
            }
            if sort_field not in valid_sort_fields:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort field. Must be one of {valid_sort_fields}")

            if sort_order not in {1, -1}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sort order must be 1 (ascending) or -1 (descending)")

            total_documents = await self.get_collection().count_documents(query_filter)
            total_pages = (total_documents + limit - 1) // limit if total_documents > 0 else 1

            cursor = self.get_collection().find(query_filter) \
                .sort(sort_field, sort_order) \
                .skip(skip) \
                .limit(limit)

            documents = await cursor.to_list(length=limit)

            return DocumentPaginationResponse(
                total=total_documents,
                page=page,
                limit=limit,
                pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
                documents=[DocumentInDB(**doc) for doc in documents]
            )
        except Exception as e:
            handle_service_exception(e)

    async def delete_document(self, document_id: str, username: str) -> dict:
        try:
            document_id = to_object_id(document_id)
            document = await self.get_collection().find_one({"_id": document_id})
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

            is_admin = await AdminService().is_admin(username)
            if not is_admin and not await self.is_your_document(document_id, username):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to delete this document")

            if document.get("file_id"):
                for attempt in range(3):
                    try:
                        await self.gridfs_bucket.delete(to_object_id(document["file_id"]))
                        break
                    except Exception as e:
                        logger.warning(f"Attempt {attempt+1} failed to delete GridFS file {document['file_id']}: {str(e)}")
                        if attempt == 2:
                            logger.error(f"Failed to delete GridFS file {document['file_id']} after retries")

            result = await self.get_collection().delete_one({"_id": document_id})
            if result.deleted_count == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete document")

            return {"message": "Document deleted successfully"}
        except Exception as e:
            handle_service_exception(e)

    async def bulk_delete_documents(self, bulk_delete: BulkDeleteRequest, current_user_data: AuthInAdminDB) -> dict:
        try:
            if not current_user_data.is_admin:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can perform bulk delete operations")

            document_ids = [to_object_id(doc_id) for doc_id in bulk_delete.document_ids]
            documents = await self.get_collection().find({"_id": {"$in": document_ids}}).to_list(length=len(document_ids))
            if len(documents) != len(document_ids):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more documents not found")

            for doc in documents:
                if doc.get("file_id"):
                    for attempt in range(3):
                        try:
                            await self.gridfs_bucket.delete(to_object_id(doc["file_id"]))
                            break
                        except Exception as e:
                            logger.warning(f"Attempt {attempt+1} failed to delete GridFS file {doc['file_id']}: {str(e)}")
                            if attempt == 2:
                                logger.error(f"Failed to delete GridFS file {doc['file_id']} after retries")

            result = await self.get_collection().delete_many({"_id": {"$in": document_ids}})
            return {
                "message": f"Successfully deleted {result.deleted_count} documents",
                "deleted_count": result.deleted_count
            }
        except Exception as e:
            handle_service_exception(e)

    async def bulk_update_status(self, bulk_update: BulkUpdateStatusRequest, current_user_data: AuthInAdminDB) -> dict:
        try:
            if not current_user_data.is_admin:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can perform bulk status updates")

            document_ids = [to_object_id(doc_id) for doc_id in bulk_update.document_ids]
            existing_docs = await self.get_collection().count_documents({"_id": {"$in": document_ids}})
            if existing_docs != len(document_ids):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more documents not found")

            valid_statuses = {"Not Filed", "Filed", "Suspended"}
            if bulk_update.status not in valid_statuses:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of {valid_statuses}")

            update_data = {
                "status": bulk_update.status,
                "filed_by": current_user_data.username if bulk_update.status == "Filed" else None,
                "filed_date": datetime.now() if bulk_update.status == "Filed" else None
            }

            result = await self.get_collection().update_many(
                {"_id": {"$in": document_ids}},
                {"$set": update_data}
            )

            return {
                "message": f"Successfully updated {result.modified_count} documents",
                "updated_count": result.modified_count
            }
        except Exception as e:
            handle_service_exception(e)

    async def is_your_document(self, doc_id: str, username: str) -> bool:
        try:
            doc_id = to_object_id(doc_id)
            document = await self.get_collection().find_one({"_id": doc_id, "created_by": username})
            return document is not None
        except Exception as e:
            handle_service_exception(e)

    @staticmethod
    async def ensure_indexes() -> None:
        try:
            await DocumentModel.ensure_indexes()
        except Exception as e:
            handle_service_exception(e)

    async def bulk_create_documents(self, documents: List[DocumentCreate]) -> List[DocumentInDB]:
        try:
            db = MongoDB.get_database()
            if db is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")

            created_documents = []
            year = datetime.now().year

            for document in documents:
                document.department_id = to_object_id(document.department_id)
                document.document_type_id = to_object_id(document.document_type_id)
                dept_check = await db["departments"].find_one({
                    "_id": document.department_id,
                    "document_types._id": document.document_type_id
                })
                if not dept_check:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid department_id or document_type_id for {document.title}")

                cursor = db["departments"].aggregate([
                    {"$match": {"_id": document.department_id}},
                    {"$unwind": "$document_types"},
                    {"$match": {"document_types._id": document.document_type_id}},
                    {"$project": {"prefix": "$document_types.prefix", "padding": "$document_types.padding"}}
                ])
                doc_type = await cursor.to_list(length=1)
                if not doc_type:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Document type not found for {document.title}")
                doc_type = doc_type[0]

                counter_doc = await db["sequence_counters"].find_one_and_update(
                    {
                        "department_id": document.department_id,
                        "document_type_id": document.document_type_id,
                        "year": year
                    },
                    {"$inc": {"sequence_value": 1}},
                    upsert=True,
                    return_document=True
                )
                if not counter_doc.get("sequence_value"):
                    counter_doc["sequence_value"] = 1
                    counter_doc["padding"] = doc_type.get("padding", 2)
                seq_str = str(counter_doc["sequence_value"])
                padded_seq = seq_str if len(seq_str) > counter_doc.get("padding", 2) else seq_str.zfill(counter_doc.get("padding", 2))

                year_suffix = str(year % 100)
                ref_no = f"{doc_type['prefix']}/{padded_seq}/{year_suffix}"

                existing = await self.get_collection().find_one({"ref_no": ref_no})
                if existing:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Reference number {ref_no} exists")

                document_data = document.model_dump()
                document_data.update({
                    "_id": ObjectId(),
                    "ref_no": ref_no,
                    "created_date": datetime.now(),
                    "status": "Not Filed",
                    "created_by": document_data.get("created_by"),
                })

                created_documents.append(document_data)

            result = await self.get_collection().insert_many(created_documents)
            inserted_docs = [DocumentInDB(**doc_data) for doc_data in created_documents]
            return inserted_docs
        except Exception as e:
            handle_service_exception(e)

    async def download_document(self, document_id: str,  gridfs_bucket: AsyncIOMotorGridFSBucket ,current_user: AuthInAdminDB):
        try:
            document = await self.get_document_by_id(document_id)
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            if not document.file_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file associated with this document")

            is_admin = current_user.is_admin
            if not is_admin and not await self.is_your_document(document_id, current_user.full_name):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to download this document")

            file_id = to_object_id(document.file_id)
            files_collection_name = f"{settings.GRIDFS_BUCKET_NAME}.files"
            file_info = await self.get_file_collection(files_collection_name).find_one({"_id": file_id})
            if not file_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found in GridFS")

            gridfs_file = await gridfs_bucket.open_download_stream(file_id)

            content_type = (
                gridfs_file.metadata.get("content_type", "application/octet-stream")
                if gridfs_file.metadata else "application/octet-stream"
            )
            filename = gridfs_file.filename or "document"
            extension = mimetypes.guess_extension(content_type) or ""
            if extension and not filename.lower().endswith(extension.lower()):
                filename += extension

            filename = filename.replace("\n", "").replace("\r", "").replace(";", "")

            return StreamingResponse(
                AsyncIteratorWrapper(gridfs_file),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(gridfs_file.length)
                }
            )
        except Exception as e:
            handle_service_exception(e)


    async def count_docs_by_status(self, department_id: str) -> Dict[str, int]:
        try:
            department_id = to_object_id(department_id)
            pipeline = [
                {"$match": {"department_id": department_id}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            results = await self.get_collection().aggregate(pipeline).to_list(length=None)

            status_counts = {result["_id"]: result["count"] for result in results}
            return {
                "Not Filed": status_counts.get("Not Filed", 0),
                "Filed": status_counts.get("Filed", 0),
                "Suspended": status_counts.get("Suspended", 0)
            }
        except Exception as e:
            handle_service_exception(e)

   