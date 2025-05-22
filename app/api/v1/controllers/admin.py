from typing import List

from fastapi import HTTPException
from app.services.admin import AdminService
from app.schemas.admin import AdminUser
from app.core.exceptions import handle_service_exception

class AdminController:
    @staticmethod
    async def get_all_users() -> List[AdminUser]:
        return await AdminService().get_all_users()

    @staticmethod
    async def create_user(user: AdminUser) -> AdminUser:
        return await AdminService().create_user(user)

    @staticmethod
    async def get_user_by_username(username: str) -> AdminUser:
        try:
            user = await AdminService().get_user_by_username(username)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except Exception as e:
            handle_service_exception(e)