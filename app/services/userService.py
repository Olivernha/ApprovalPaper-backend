from fastapi import HTTPException, status
from ..database.DBconnection import MongoDB
from ..models.admin import AdminUser as User

class UserService:
    collection_name = "users"
    
    @staticmethod
    def get_collection():
        return MongoDB.get_database()[UserService.collection_name]
    
    @staticmethod
    async def get_user_by_username(username: str) -> User | None:
        """Get a user by username."""
        user = await UserService.get_collection().find_one({"username": username})
        if user is None:
            return None
        return User(**user)

    @staticmethod
    async def create_user(user: dict) -> User:
        """Create a new user in the database."""
        existing_user = await UserService.get_user_by_username(user.get("username"))
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        
        result = await UserService.get_collection().insert_one(user)
        return User(**{"_id": str(result.inserted_id), **user})
