from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from .base import PyObjectId

class AdminUser(BaseModel):
    """User model with only username for the admin collection"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id", description="Unique identifier for the user")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "username": "admin_user"
            }
        }
    )