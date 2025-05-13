# app/controllers/user_controller.py
from typing import List, Optional
from fastapi import HTTPException, status

from ..models.admin import AdminUser
# from ..services.user_service import UserService


class UserController:
    @staticmethod
    async def get_all_users() -> List[AdminUser]:
        """Get all users"""
        try:
            # give dummy data for now
            users = [
                AdminUser(username="admin1"),
                AdminUser(username="admin2"),
                AdminUser(username="admin3"),
            ]
            return users
          
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 
    
  