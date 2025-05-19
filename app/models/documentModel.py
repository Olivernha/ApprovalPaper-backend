from app.database import MongoDB

class DocumentModel:
    COLLECTION_NAME = "documents"

    @staticmethod
    async def ensure_indexes() -> None:
        """Create indexes for the document collection"""
        db = MongoDB.get_database()
        await db[DocumentModel.COLLECTION_NAME].create_index("document_type_id")
        await db[DocumentModel.COLLECTION_NAME].create_index("department_id")
        await db[DocumentModel.COLLECTION_NAME].create_index("ref_no", unique=True)
