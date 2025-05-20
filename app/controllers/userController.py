from typing import List
from fastapi import HTTPException, status
from app.services.adminService import AdminService
from app.schema.admin import AdminUser


class UserController:
    COLLECTION_NAME = "users"

    @staticmethod
    async def get_all_users(collection_name: str = COLLECTION_NAME) -> List[AdminUser]:
        """Retrieve all users."""
        try:
            service = AdminService(collection_name=collection_name)
            users = await service.get_collection().find().to_list(length=None)
            return [AdminUser(**user) for user in users]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to fetch users: {str(e)}")

    @staticmethod
    async def create_user(user: AdminUser, collection_name: str = COLLECTION_NAME) -> AdminUser:
        """Create a new user."""
        try:
            service = AdminService(collection_name=collection_name)
            return await service.create_user(user)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to create user: {str(e)}")

    @staticmethod
    async def get_user_by_username(username: str, collection_name: str = COLLECTION_NAME) -> AdminUser:
        """Get a user by username."""
        try:
            service = AdminService(collection_name=collection_name)
            user = await service.get_user_by_username(username)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return user
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to fetch user: {str(e)}")