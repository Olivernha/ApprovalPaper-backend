from ..database.DBconnection import MongoDB
from ..schema.document import DocumentInDB

class DocumentModel:
    """MongoDB-specific logic for the documents collection"""
    COLLECTION_NAME = "documents"

    @classmethod
    async def ensure_indexes(cls):
        """Create indexes for the documents collection"""
        db = MongoDB.get_database()
        await db[cls.COLLECTION_NAME].create_index("ref_no", unique=True)
    
    @classmethod
    async def to_document(cls, document: dict) -> DocumentInDB:
        """Convert MongoDB document to DocumentInDB model"""
        if not document:
            return None
        document = document.copy()
        document["_id"] = str(document["_id"])
        document["document_type_id"] = str(document["document_type_id"])
        document["department_id"] = str(document["department_id"])
        document["created_by"] = str(document["created_by"])
        if document.get("filed_by"):
            document["filed_by"] = str(document["filed_by"])
        return DocumentInDB(**document)