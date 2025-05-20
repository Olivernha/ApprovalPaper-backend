from app.database import MongoDB

class UserModel:
    COLLECTION_NAME = "users"

    @staticmethod
    async def ensure_indexes() -> None:
        """Create indexes for the users collection"""
        db = MongoDB.get_database()
        await db[UserModel.COLLECTION_NAME].create_index("username", unique=True)