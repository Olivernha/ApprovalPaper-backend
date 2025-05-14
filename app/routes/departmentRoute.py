from fastapi import APIRouter

from app.controllers import DepartmentController
from app.schema import  DepartmentCreate

router = APIRouter(
    prefix="/department", 
    tags=["department"]
)

@router.post("/create", status_code=201)
async def create_department(department : DepartmentCreate):
    return await DepartmentController.create_department(department)