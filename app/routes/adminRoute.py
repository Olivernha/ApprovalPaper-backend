from fastapi import APIRouter, status
from typing import List
from ..schema import AdminUser
from ..controllers import UserController
from ..config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[AdminUser])
async def get_users():
    return await UserController.get_all_users(collection_name="users")

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AdminUser)
async def create_user(user: AdminUser):
    return await UserController.create_user(user, collection_name="users")

@router.get("/{username}", response_model=AdminUser)
async def get_user(username: str):
    print(f"Fetching user with username: {username}")
    return await UserController.get_user_by_username(username, collection_name="users")