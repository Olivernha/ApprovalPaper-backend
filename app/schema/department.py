from bson import ObjectId
from pydantic import BaseModel, Field, root_validator
from typing import Any, Optional

from .base import PyObjectId

class Department(BaseModel):
    """Shared base class, useful for inheritance across department models."""
    class Config:
        """Configuration for shared behavior across models."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}  # Convert PyObjectId to string
        json_schema_extra = {
            "example": {
                "name": "Finance"
            }
        }

class DepartmentCreate(Department):
    """Department model used when creating a new department (POST request)."""
    name: str = Field(..., min_length=1, description="Unique department name (e.g., Finance)")


class DepartmentInDB(Department):
    """Department model for MongoDB interaction (includes _id)."""
    id: Optional[PyObjectId] = Field(alias="_id")
    name: str = Field(..., min_length=1, description="Unique department name (e.g., Finance)")

class DepartmentResponse(DepartmentInDB):
    pass
