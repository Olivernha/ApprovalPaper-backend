from typing import List
from fastapi import HTTPException, status

from app.services.adminService import AdminService
from ..models.admin import AdminUser

class UserController:
    @staticmethod
    async def get_all_users() -> List[AdminUser]:
        try:
            users = await AdminService.get_collection().find().to_list(length=100)
            return users
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    @staticmethod
    async def create_user(user: AdminUser) -> AdminUser:
        try:
            user_data = user.model_dump()
            created_user = await AdminService.create_user(user_data)
            print(f"Created user: {created_user}")
            return created_user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    async def get_user_by_username(username: str) -> AdminUser:
        try:
            user = await AdminService.get_user_by_username(username)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))