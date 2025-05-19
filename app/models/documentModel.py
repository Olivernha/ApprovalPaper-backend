from app.database import MongoDB

class DocumentModel:
    COLLECTION_NAME = "documents"

    @staticmethod
    async def ensure_indexes() -> None:
        """Create indexes for the document collection"""
        db = MongoDB.get_database()
        
        # Basic indexes
        await db[DocumentModel.COLLECTION_NAME].create_index("document_type_id")
        await db[DocumentModel.COLLECTION_NAME].create_index("department_id")
        await db[DocumentModel.COLLECTION_NAME].create_index("ref_no", unique=True)
        
        # Additional indexes for search and filtering
        await db[DocumentModel.COLLECTION_NAME].create_index("status")
        await db[DocumentModel.COLLECTION_NAME].create_index("created_by")
        await db[DocumentModel.COLLECTION_NAME].create_index("filed_by")
        
        # Text index for full-text search
        await db[DocumentModel.COLLECTION_NAME].create_index([
            ("title", "text"),
            ("ref_no", "text"),
            ("created_by", "text")
        ])
        
        # Compound indexes for common query patterns
        await db[DocumentModel.COLLECTION_NAME].create_index([
            ("department_id", 1),
            ("status", 1)
        ])
        
        await db[DocumentModel.COLLECTION_NAME].create_index([
            ("document_type_id", 1),
            ("status", 1)
        ])
        
        # Indexes for sorting
        await db[DocumentModel.COLLECTION_NAME].create_index("created_date")
        await db[DocumentModel.COLLECTION_NAME].create_index("filed_date")