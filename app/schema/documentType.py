from typing import List
from pydantic import Field, BaseModel


from .base import PyObjectId
class DocumentType(BaseModel):
    """Base model for embedded document type"""
    name: str = Field(..., description="Name of the document type")
    prefix: str = Field(..., description="Prefix for document numbering")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Invoice",
                "prefix": "INV"
            }
        }

class DocumentTypeCreate(DocumentType):
    """Schema for creating a document type"""
    pass

class DocumentTypeInDB(DocumentType):
    """Schema for document type in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


   