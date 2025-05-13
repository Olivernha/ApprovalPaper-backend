# app/models/user.py
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field
from bson import ObjectId

PyObjectId = Annotated[str, BeforeValidator(str)]
# Admin user model
class AdminUser(BaseModel):
    """Admin user model"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    
    class Config:    
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "username": "admin",
            }
        }

