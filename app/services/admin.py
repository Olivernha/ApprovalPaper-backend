from fastapi import HTTPException, status
from bson import ObjectId

from app.core.database import MongoDB
from app.schemas.admin import AdminUser
from app.core.exceptions import handle_service_exception

class AdminService:
    def __init__(self, collection_name: str = "admins"):
        self.collection_name = collection_name

    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]

    async def get_user_by_username(self, username: str) -> AdminUser | None:
        try:
            if not username or len(username.strip()) < 3:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username")
            user = await self.get_collection().find_one({"username": username.strip()})
            return AdminUser(**user) if user else None
        except Exception as e:
            handle_service_exception(e)

    async def is_admin(self, username: str) -> bool:
       
        user = await self.get_user_by_username(username)
        return user is not None

    async def create_user(self, user: AdminUser) -> AdminUser:
        try:
            existing_user = await self.get_user_by_username(user.username)
            if existing_user:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

            user_data = user.model_dump(by_alias=True)
            user_data["_id"] = ObjectId()
            await self.get_collection().insert_one(user_data)
            return AdminUser(**user_data)
        except Exception as e:
            handle_service_exception(e)

    async def get_all_users(self) -> list[AdminUser]:
        try:
            users = await self.get_collection().find().to_list(length=100)
            return [AdminUser(**user) for user in users]
        except Exception as e:
            handle_service_exception(e)