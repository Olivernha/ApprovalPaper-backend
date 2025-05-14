from typing import Annotated, Optional
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId

from schema import PyObjectId

class DocumentType(BaseModel):
    """Document Type model for categorizing documents"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., min_length=1, description="Unique document type name (e.g., Tender Committee)")
    prefix: str = Field(..., min_length=1, description="Unique prefix for reference number (e.g., TPG)")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Tender Committee",
                "prefix": "TPG"
            }
        }
    }
       