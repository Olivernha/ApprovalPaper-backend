
from fastapi import APIRouter, Depends, status, Query
from typing import List

from ..models.admin import AdminUser
from ..controllers.userController import UserController
from ..config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)



@router.get("/", response_model=List[AdminUser])
async def get_users():
    return await UserController.get_all_users()


@router.post("/",status_code=status.HTTP_201_CREATED, response_model=AdminUser)
async def create_user(user: AdminUser):
    return await UserController.create_user(user)
