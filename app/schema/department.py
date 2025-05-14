from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field

# Annotated ObjectId type
PyObjectId = Annotated[str, BeforeValidator(str)]

class Department(BaseModel):
    """Department model for categorizing documents"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., min_length=1, description="Unique department name (e.g., Finance)")


    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {PyObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "Finance"
            }
        }
    }


class DepartmentCreate(BaseModel):
    """Department model for creating a new department"""
    name: str = Field(..., min_length=1, description="Unique department name (e.g., Finance)")