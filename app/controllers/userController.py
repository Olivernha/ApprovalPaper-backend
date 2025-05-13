from typing import List
from fastapi import HTTPException, status

from app.services.adminService import UserService
from ..models.admin import AdminUser

class UserController:
    @staticmethod
    async def get_all_users() -> List[AdminUser]:
        try:
            users = await UserService.get_collection().find().to_list(length=100)
            return users
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    @staticmethod
    async def create_user(user: AdminUser) -> AdminUser:
        try:
            user_data = user.model_dump()
            created_user = await UserService.create_user(user_data)
            print(f"Created user: {created_user}")
            return created_user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
