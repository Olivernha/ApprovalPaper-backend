from datetime import datetime
from typing import List
from fastapi import HTTPException, status
from bson import ObjectId
from pydantic import ValidationError
from ..database.DBconnection import MongoDB
from ..schema.document import DocumentCreate, DocumentInDB
from ..models import DocumentModel

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

            # Validate references
            doc_type = await db["document_types"].find_one({"_id": ObjectId(document.document_type_id)})
            if not doc_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document_type_id")

            if not await db["departments"].find_one({"_id": ObjectId(document.department_id)}):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department_id")

            # Generate auto ref_no
            year = datetime.now().year
            counter_doc = await db["sequence_counters"].find_one_and_update(
                {
                    "department_id": str(document.department_id),
                    "document_type_id": str(document.document_type_id),
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

            # Check for existing ref_no
            existing = await self.get_collection().find_one({"ref_no": ref_no})
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference number exists")

            # Prepare document data
            document_data = document.model_dump()
            print(f'document_data: {document_data}')  # Add this line to print the document_data)
            document_data.update({
                "ref_no": ref_no,
                "created_date": datetime.now(),
                "status": document_data.get("status", "Not Filed"),
                "created_by": document_data.get("created_by"),
            })
            # i want to add filed_by field to the document_data
            document_data["status"] = "Not Filed"
            document_data["created_date"] = datetime.now()
            result = await self.get_collection().insert_one(document_data)

            # Return document with inserted ID
            return await DocumentModel.to_document({"_id": result.inserted_id, **document_data})

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create document: {str(e)}")

    async def get_documents(self) -> List[DocumentInDB]:
        """Retrieve all documents"""
        try:
            results = self.get_collection().find()
            documents = await results.to_list(length=100)
            return [await DocumentModel.to_document(doc) for doc in documents]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch documents: {str(e)}")

    @staticmethod
    async def ensure_indexes() -> None:
        """Ensure indexes for the documents collection"""
        try:
            await DocumentModel.ensure_indexes()
        except Exception as e:
            raise