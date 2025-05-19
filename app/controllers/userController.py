from typing import List
from fastapi import HTTPException, status
from app.services.adminService import AdminService
from ..schema.admin import AdminUser

class UserController:
    @staticmethod
    async def get_all_users(collection_name: str = "users") -> List[AdminUser]:
        try:
            service = AdminService(collection_name=collection_name)
            users = await service.get_collection().find().to_list(length=100)
            return users
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    @staticmethod
    async def create_user(user: AdminUser, collection_name: str = "users") -> AdminUser:
        try:
            service = AdminService(collection_name=collection_name)
            user_data = user.model_dump()
            created_user = await service.create_user(user_data)
            return created_user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def get_user_by_username(username: str, collection_name: str = "users") -> AdminUser:
        try:
            service = AdminService(collection_name=collection_name)
            user = await service.get_user_by_username(username)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    
  
