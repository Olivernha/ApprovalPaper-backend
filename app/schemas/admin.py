from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.base import PyObjectId

class AdminUser(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id", description="Unique identifier for the user")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str},
        json_schema_extra={
            "example": {
                "username": "admin_user"
            }
        }
    )

class AuthInAdminDB(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name of the user")
    is_admin: bool = Field(..., description="Is the user an admin")


class AdminResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str},
        json_schema_extra={
            "example": {
                "username": "admin_user"
            }
        }
    )