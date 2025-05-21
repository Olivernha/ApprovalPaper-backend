

from app.core.database import MongoDB


class DocumentModel:
    COLLECTION_NAME = "documents"

    @staticmethod
    async def ensure_indexes() -> None:
        db = MongoDB.get_database()
        await db[DocumentModel.COLLECTION_NAME].create_index("document_type_id")
        await db[DocumentModel.COLLECTION_NAME].create_index("department_id")
        await db[DocumentModel.COLLECTION_NAME].create_index("ref_no", unique=True)
        await db[DocumentModel.COLLECTION_NAME].create_index("status")
        await db[DocumentModel.COLLECTION_NAME].create_index("created_by")
        await db[DocumentModel.COLLECTION_NAME].create_index("filed_by")
        await db[DocumentModel.COLLECTION_NAME].create_index([
            ("title", "text"),
            ("ref_no", "text"),
            ("created_by", "text")
        ])
        await db[DocumentModel.COLLECTION_NAME].create_index([
            ("department_id", 1),
            ("status", 1)
        ])
        await db[DocumentModel.COLLECTION_NAME].create_index([
            ("document_type_id", 1),
            ("status", 1)
        ])
        await db[DocumentModel.COLLECTION_NAME].create_index("created_date")
        await db[DocumentModel.COLLECTION_NAME].create_index("filed_date")