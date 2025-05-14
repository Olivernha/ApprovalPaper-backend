from fastapi import HTTPException, status
from bson import ObjectId
from ..database import MongoDB
from ..schema import DocumentTypeCreate, DocumentTypeInDB
from ..models import DocumentTypeModel

class DocumentTypeService:
    def __init__(self, collection_name: str = DocumentTypeModel.COLLECTION_NAME):
        self.collection_name = collection_name
    
    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]
    
    async def create_document_type(self, doc_type: DocumentTypeCreate) -> DocumentTypeInDB:
        """Create a new document type"""
        db = MongoDB.get_database()
        if not await db["departments"].find_one({"_id": ObjectId(doc_type.department_id)}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department_id")
        
        existing = await self.get_collection().find_one({"name": doc_type.name})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document type name exists")
        existing = await self.get_collection().find_one({"prefix": doc_type.prefix})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prefix exists")
        
        doc_type_data = doc_type.model_dump()
        result = await self.get_collection().insert_one(doc_type_data)
        return await DocumentTypeModel.to_document_type({"_id": result.inserted_id, **doc_type_data})
    
    @staticmethod
    async def ensure_indexes():
        """Ensure indexes for the document_types collection"""
        await DocumentTypeModel.ensure_indexes()