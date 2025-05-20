from fastapi import APIRouter, status
from typing import List
from ..schema.admin import AdminUser
from ..controllers.userController import UserController
from ..config.settings import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"],
    responses={
        404: {"description": "User not found"},
        409: {"description": "Username already exists"},
        500: {"description": "Internal server error"}
    }
)

@router.get("/", response_model=List[AdminUser])
async def get_users():
    return await UserController.get_all_users()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AdminUser)
async def create_user(user: AdminUser):
    return await UserController.create_user(user)

@router.get("/{username}", response_model=AdminUser)
async def get_user(username: str):
    print(f"Fetching user with username: {username}")
    return await UserController.get_user_by_username(username)