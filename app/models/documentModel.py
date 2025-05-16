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
    