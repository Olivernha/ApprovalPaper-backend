
from bson import ObjectId

from app.database import MongoDB
from app.schema.department import DepartmentInDB


class DepartmentModel:
    COLLECTION_NAME = "departments"

    @classmethod
    async def ensure_indexes(cls) -> None:
        """Create indexes for the department collection"""
        db = MongoDB.get_database()
        await db[cls.COLLECTION_NAME].create_index("name", unique=True)
        await db[cls.COLLECTION_NAME].create_index("document_types.name", sparse=True)
        await db[cls.COLLECTION_NAME].create_index("document_types.prefix", unique=True, sparse=True)
