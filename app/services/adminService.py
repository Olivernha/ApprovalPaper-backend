from fastapi import HTTPException, status
from ..database import MongoDB
from ..schema import AdminUser


class AdminService:
    def __init__(self, collection_name: str = "users"):
        self.collection_name = collection_name
    
    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]
    
    async def get_user_by_username(self, username: str) -> AdminUser | None:
        """Get a user by username."""
        user = await self.get_collection().find_one({"username": username})
        if user is None:
            return None
        return AdminUser(**user)  
    async def create_user(self, user: dict) -> AdminUser:
        """Create a new user in the database."""
        existing_user = await self.get_user_by_username(user.get("username"))
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
  
        
        await self.get_collection().insert_one(user)  
        return user