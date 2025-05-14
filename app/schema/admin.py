from typing import Annotated, Optional
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


# Annotated ObjectId type
PyObjectId = Annotated[str, BeforeValidator(str)]

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
