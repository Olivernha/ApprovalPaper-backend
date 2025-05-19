from typing import  Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from .base import PyObjectId

class AdminUser(BaseModel):
    """Admin user model"""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    username: str

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "username": "admin"
            }
        }
    }
