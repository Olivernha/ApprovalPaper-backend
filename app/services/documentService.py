from datetime import datetime
from typing import List
from fastapi import HTTPException, status
from bson import ObjectId

from app.schema.base import PyObjectId
from app.services.adminService import AdminService
from app.services.departmentService import DepartmentService
from ..database.DBconnection import MongoDB
from ..schema.document import DocumentCreate, DocumentInDB, DocumentResponse, DocumentUpdateAdmin, DocumentUpdateNormal
from ..models.documentModel import DocumentModel

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
            doc_type = await db["document_types"].find_one({"_id": document.document_type_id})
            if not doc_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document_type_id")

            if not await db["departments"].find_one({"_id": document.department_id}):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department_id")

            # Generate auto ref_no
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
                "created_date":  datetime.now(),
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

    @staticmethod
    async def ensure_indexes() -> None:
        """Ensure indexes for the documents collection"""
        try:
            await DocumentModel.ensure_indexes()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ensure indexes: {str(e)}")
        

    async def update_document(self, document_id: str, update_data: DocumentUpdateNormal | DocumentUpdateAdmin) -> DocumentResponse:
        """Update a document based on user role"""
        try:
            # Validate document exists
            document = await self.get_collection().find_one({"_id": ObjectId(document_id)})
            if not document:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

            username = update_data.current_user
            is_admin = await AdminService().is_admin(username)

            # Check if normal user is the creator
            if not is_admin and (not username or not await self.is_your_document(document_id, username)):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to update this document")

            # Prepare update data
            update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

            # Handle admin-specific fields
            if is_admin and isinstance(update_data, DocumentUpdateAdmin):
                # Convert date strings to datetime
                if update_dict.get("created_date"):
                    update_dict["created_date"] = datetime.strptime(update_dict["created_date"], "%d/%m/%Y")
                if update_dict.get("filed_date"):
                    update_dict["filed_date"] = datetime.strptime(update_dict["filed_date"], "%d/%m/%Y")
            else:
                # Restrict to normal user fields
                if not isinstance(update_data, DocumentUpdateNormal):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin fields not allowed for normal users")
                allowed_fields = {"title", "document_type_id", "department_id", "current_user"}
                if any(field not in allowed_fields for field in update_dict):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Normal users can only update title, document_type_id, and department_id",
                    )

            # Convert IDs to ObjectId
            if "document_type_id" in update_dict:
                update_dict["document_type_id"] = ObjectId(update_dict["document_type_id"])
            if "department_id" in update_dict:
                update_dict["department_id"] = ObjectId(update_dict["department_id"])

            # Remove current_user from update
            update_dict.pop("current_user", None)
            print(update_dict)
            # Update document
            result = await self.get_collection().update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_dict},
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes applied")

            # Fetch the updated document
            updated_document = await self.get_collection().find_one({"_id": ObjectId(document_id)})
            return DocumentResponse(**updated_document)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update document: {str(e)}")

    async def is_your_document(self, doc_id: str, username: str) -> bool:
        """Check if the document was created by the given username"""
        try:
            document = await self.get_collection().find_one({"_id": ObjectId(doc_id), "created_by": username})
            return document is not None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to check document: {str(e)}")

