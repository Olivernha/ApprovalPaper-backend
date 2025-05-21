from fastapi import APIRouter, status
from typing import List
from app.api.v1.controllers.admin import AdminController
from app.schemas.admin import AdminUser
from app.core.config import settings

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
    return await AdminController.get_all_users()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AdminUser)
async def create_user(user: AdminUser):
    return await AdminController.create_user(user)

@router.get("/{username}", response_model=AdminUser)
async def get_user(username: str):
    return await AdminController.get_user_by_username(username)