from fastapi import HTTPException, status
from ..database.DBconnection import MongoDB
from ..models.admin import AdminUser 
class AdminService:
    collection_name = "users"
    
    @staticmethod
    def get_collection():
        return MongoDB.get_database()[AdminService.collection_name]
    
    @staticmethod
    async def get_user_by_username(username: str) -> AdminUser | None:
        """Get a user by username."""
        user = await AdminService.get_collection().find_one({"username": username})
        if user is None:
            return None
        return AdminUser(**user)

    @staticmethod
    async def create_user(user: dict) -> AdminUser:
        """Create a new user in the database."""
        existing_user = await AdminService.get_user_by_username(user.get("username"))
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        
        result = await AdminService.get_collection().insert_one(user)
        return AdminUser(_id=str(result.inserted_id), **user)
