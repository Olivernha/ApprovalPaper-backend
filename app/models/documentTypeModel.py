from ..database import MongoDB
from ..schema import DocumentTypeInDB ,DocumentTypeWithDepartment

class DocumentTypeModel:
    COLLECTION_NAME = "document_types"
    @classmethod
    async def ensure_indexes(cls):
        """Create indexes for the document_types collection"""
        db = MongoDB.get_database()
        await db[cls.COLLECTION_NAME].create_index("name", unique=True)
        await db[cls.COLLECTION_NAME].create_index("prefix", unique=True)
    
    @classmethod
    async def to_document_type(cls, document: dict) -> DocumentTypeInDB:
        """Convert MongoDB document to DocumentTypeInDB model"""
        if not document:
            return None
        document["_id"] = str(document["_id"])
        document["department_id"] = str(document["department_id"])
        return DocumentTypeInDB(**document)
    
    @classmethod
    async def to_document_type_with_department(cls, document: dict) -> DocumentTypeWithDepartment:
        """Convert MongoDB document with department lookup to DocumentTypeWithDepartment model"""
        if not document:
            return None
        document["_id"] = str(document["_id"])
        document["department_id"] = str(document["department_id"])
        document["department"] = {
            "_id": str(document["department"][0]["_id"]),
            "name": document["department"][0]["name"]
        } if document.get("department") else None
        return DocumentTypeWithDepartment(**document)