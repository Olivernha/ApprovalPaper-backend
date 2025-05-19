from datetime import datetime
from typing import List, Union, Dict, Any, Optional
from fastapi import HTTPException, status
from bson import ObjectId

from app.schema.base import PyObjectId
from app.services.adminService import AdminService
from app.database import MongoDB
from app.schema.document import (
    BulkDeleteRequest,
    BulkUpdateStatusRequest,
    DocumentCreate,
    DocumentInDB,
    DocumentResponse,
    DocumentUpdateAdmin,
    DocumentUpdateNormal,
    DocumentPaginationResponse,
)
from app.models.documentModel import DocumentModel

class DocumentService:
    def __init__(self, collection_name: str = DocumentModel.COLLECTION_NAME):
        self.collection_name = collection_name

    def get_collection(self):
        collection = MongoDB.get_database()[self.collection_name]
        return collection

    async def create_document(self, document: DocumentCreate) -> DocumentInDB:
        """Create a new document"""
        try:
            db = MongoDB.get_database()
            if db is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")

            document.department_id = PyObjectId(document.department_id)
            document.document_type_id = PyObjectId(document.document_type_id)
            if not await db["departments"].find_one({"_id": document.department_id} , {"document_types": {"$elemMatch": {"_id": document.document_type_id}}}):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department_id")
           # i want to get prefix from department.document_types by document_type_id
            cursor = db["departments"].aggregate([
                {"$match": {"_id": document.department_id}},
                {"$unwind": "$document_types"},
                {"$match": {"document_types._id": document.document_type_id}},
                {"$project": {"prefix": "$document_types.prefix"}}
            ])
            doc_type = await cursor.to_list(length=1)
            if not doc_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document type not found")
            doc_type = doc_type[0]

            year = datetime.now().year
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
                counter_doc["padding"] = 3

            padded_seq = str(counter_doc["sequence_value"]).zfill(counter_doc.get("padding", 3))
            year_suffix = str(year % 100)
            ref_no = f"{doc_type['prefix']}/{padded_seq}/{year_suffix}"

            existing = await self.get_collection().find_one({"ref_no": ref_no})
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference number exists")

            document_data = document.model_dump()

            document_data.update({
                "ref_no": ref_no,
                "created_date": datetime.now(),
                "status": document_data.get("status", "Not Filed"),
                "created_by": document_data.get("created_by"),
            })
        
            document_data["status"] = "Not Filed"
            document_data["created_date"] = datetime.now()

            result = await self.get_collection().insert_one(document_data)
            document_data["_id"] = result.inserted_id
            return DocumentInDB(**document_data)

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create document: {str(e)}")

    async def get_documents(self) -> List[DocumentInDB]:
        """Retrieve all documents"""
        try:
            results = self.get_collection().find()
            documents = await results.to_list(length=100)
            return [DocumentInDB(**doc) for doc in documents]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch documents: {str(e)}")

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
        """
        Retrieve documents with pagination and search filtering
        
        Args:
            page: Current page number (starts from 1)
            limit: Number of documents per page
            search: Search query for title or ref_no
            status_filter: Filter by document status
            department_id: Filter by department ID
            document_type_id: Filter by document type ID
            sort_field: Field to sort by
            sort_order: Sort order (1 for ascending, -1 for descending)
            
        Returns:
            Paginated document response
        """
        try:
            # Calculate skip value
            skip = (page - 1) * limit
            
            # Build query filter
            query_filter: Dict[str, Any] = {}
            
            # Add search filter
            if search:
                query_filter["$or"] = [
                    {"title": {"$regex": search, "$options": "i"}},
                    {"ref_no": {"$regex": search, "$options": "i"}},
                    {"created_by": {"$regex": search, "$options": "i"}}
                ]
                
            # Add status filter
            if status_filter:
                valid_statuses = {"Not Filed", "Filed", "Suspended"}
                if status_filter not in valid_statuses:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid status. Must be one of {valid_statuses}"
                    )
                query_filter["status"] = status_filter
                
            # Add department filter
            if department_id:
                try:
                    query_filter["department_id"] = ObjectId(department_id)
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid department_id format"
                    )
                    
            # Add document type filter
            if document_type_id:
                try:
                    query_filter["document_type_id"] = ObjectId(document_type_id)
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid document_type_id format"
                    )
            
            # Validate sort field
            valid_sort_fields = {
                "created_date", "title", "ref_no", "status", 
                "created_by", "filed_date", "filed_by"
            }
            if sort_field not in valid_sort_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sort field. Must be one of {valid_sort_fields}"
                )
                
            # Validate sort order
            if sort_order not in {1, -1}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sort order must be 1 (ascending) or -1 (descending)"
                )
                
            # Count total documents
            total_documents = await self.get_collection().count_documents(query_filter)
            
            # Calculate total pages
            total_pages = (total_documents + limit - 1) // limit if total_documents > 0 else 1
            
            # Get paginated documents
            cursor = self.get_collection().find(query_filter)\
                .sort(sort_field, sort_order)\
                .skip(skip)\
                .limit(limit)
                
            documents = await cursor.to_list(length=limit)
            
            # Format response
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Failed to fetch paginated documents: {str(e)}"
            )

    async def update_document(self, document_id: str, update_data: Union[DocumentUpdateNormal, DocumentUpdateAdmin]) -> DocumentResponse:
        """Update a document based on user role"""
        try:
            document = await self.get_collection().find_one({"_id": ObjectId(document_id)})
            print("Document found:", document, "ID:", document_id)
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

            username = update_data.current_user
            is_admin = await AdminService().is_admin(username)

            if not is_admin and (not username or not await self.is_your_document(document_id, username)):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to update this document")

            update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

            if is_admin and isinstance(update_data, DocumentUpdateAdmin):
                if update_dict.get("status") == "Filed":
                   update_dict["filed_by"] = username or document.get("filed_by")
                   update_dict["filed_date"] = datetime.now() or document.get("filed_date")
                
                if update_dict.get("created_date"):
                    update_dict["created_date"] =  datetime.now()
            else:
                if not isinstance(update_data, DocumentUpdateNormal):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin fields not allowed for normal users")
                allowed_fields = {"title", "document_type_id", "department_id", "current_user"}
                if any(field not in allowed_fields for field in update_dict):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Normal users can only update title, document_type_id, and department_id",
                    )

            if "document_type_id" in update_dict:
                update_dict["document_type_id"] = ObjectId(update_dict["document_type_id"])
            if "department_id" in update_dict:
                update_dict["department_id"] = ObjectId(update_dict["department_id"])

            update_dict.pop("current_user", None)
            print(update_dict)
            result = await self.get_collection().update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_dict},
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes applied")

            updated_document = await self.get_collection().find_one({"_id": ObjectId(document_id)})
            return DocumentResponse(**updated_document)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update document: {str(e)}")

    async def delete_document(self, document_id: str, username: str) -> dict:
        """Delete a document based on user role"""
        try:
            document = await self.get_collection().find_one({"_id": ObjectId(document_id)})
            
            print("Document found:", document, "ID:", document_id)
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

            is_admin = await AdminService().is_admin(username)
            if not is_admin and not await self.is_your_document(document_id, username):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to delete this document",
                )

            result = await self.get_collection().delete_one({"_id": ObjectId(document_id)})
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to delete document",
                )

            return {"message": "Document deleted successfully"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete document: {str(e)}")

    async def bulk_delete_documents(self, bulk_delete: BulkDeleteRequest) -> dict:
        """Bulk delete documents (admin only)"""
        try:
            # Verify admin access
            is_admin = await AdminService().is_admin(bulk_delete.current_user)
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can perform bulk delete operations"
                )

            # Convert string IDs to ObjectId
            document_ids = [ObjectId(doc_id) for doc_id in bulk_delete.document_ids]

            # Check if all documents exist
            existing_docs = await self.get_collection().count_documents(
                {"_id": {"$in": document_ids}}
            )
            if existing_docs != len(document_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more documents not found"
                )

            # Perform bulk delete
            result = await self.get_collection().delete_many(
                {"_id": {"$in": document_ids}}
            )

            return {
                "message": f"Successfully deleted {result.deleted_count} documents",
                "deleted_count": result.deleted_count
            }
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to bulk delete documents: {str(e)}")

    async def bulk_update_status(self, bulk_update: BulkUpdateStatusRequest) -> dict:
        """Bulk update document statuses (admin only)"""
        try:
            # Verify admin access
            is_admin = await AdminService().is_admin(bulk_update.current_user)
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can perform bulk status updates"
                )

            # Convert string IDs to ObjectId
            document_ids = [ObjectId(doc_id) for doc_id in bulk_update.document_ids]

            # Check if all documents exist
            existing_docs = await self.get_collection().count_documents(
                {"_id": {"$in": document_ids}}
            )
            if existing_docs != len(document_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more documents not found"
                )

            # Validate status
            valid_statuses = {"Not Filed", "Filed", "Suspended"}
            if bulk_update.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of {valid_statuses}"
                )

            # Perform bulk update
            update_data = {
                "status": bulk_update.status,
                "filed_by": bulk_update.current_user if bulk_update.status == "Filed" else None,
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
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to bulk update documents: {str(e)}")

    async def is_your_document(self, doc_id: str, username: str) -> bool:
        """Check if the document was created by the given username"""
        try:
            document = await self.get_collection().find_one({"_id": ObjectId(doc_id), "created_by": username})
            return document is not None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to check document: {str(e)}")

    @staticmethod
    async def ensure_indexes() -> None:
        """Ensure indexes for the documents collection"""
        try:
            await DocumentModel.ensure_indexes()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ensure indexes: {str(e)}")