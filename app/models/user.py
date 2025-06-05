

from app.core.database import MongoDB


class UserModel:
    COLLECTION_NAME = "admins"

    @staticmethod
    async def ensure_indexes() -> None:
        db = MongoDB.get_database()
        await db[UserModel.COLLECTION_NAME].create_index("username", unique=True)