# app/controllers/user_controller.py
from typing import List
from fastapi import HTTPException, status

from app.services.userService import UserService

from ..models.admin import AdminUser


class UserController:
    @staticmethod
    async def get_all_users() -> List[AdminUser]:
        """Get all users"""
        try:
            users = await UserService.get_collection().find().to_list(length=None)
            return users
          
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 
    
  