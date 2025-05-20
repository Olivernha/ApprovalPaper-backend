from fastapi import HTTPException, status
from app.database import MongoDB
from app.schema.admin import AdminUser
from bson import ObjectId


class AdminService:
    def __init__(self, collection_name: str = "users"):
        self.collection_name = collection_name

    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]

    async def get_user_by_username(self, username: str) -> AdminUser | None:
        """Get a user by username."""
        if not username or len(username.strip()) < 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username")
        user = await self.get_collection().find_one({"username": username.strip()})
        if user is None:
            return None
        return AdminUser(**user)

    async def is_admin(self, username: str) -> bool:
        """Check if the user exists (considered admin)."""
        user = await self.get_user_by_username(username)
        return user is not None

    async def create_user(self, user: AdminUser) -> AdminUser:
        """Create a new user in the database."""
        existing_user = await self.get_user_by_username(user.username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        user_data = user.model_dump(by_alias=True)
        user_data["_id"] = ObjectId()

        await self.get_collection().insert_one(user_data)
        return AdminUser(**user_data)