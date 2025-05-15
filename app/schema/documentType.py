from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from .department import DepartmentInDB

from .base import PyObjectId

class DocumentType(BaseModel):
    """Base model for document type"""
    name: str = Field(..., description="Name of the document type")
    prefix: str = Field(..., description="Prefix for document numbering")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Tender Committee",
                "prefix": "TPG",
                "department_id": "507f1f77bcf86cd799439013"
            }
        }

class DocumentTypeCreate(DocumentType):
    """Schema for creating a document type"""
    department_id: PyObjectId = Field(...,  description="Department ID this document type belongs to")


class DocumentTypeInDB(DocumentType):
    """Schema for document type from the database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    department_id: PyObjectId = Field(..., description="Department ID this document type belongs to")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "60d5f484f1a2c8b8e4f3c8b9",
                "name": "Invoice",
                "prefix": "INV",
                "department_id": "60d5f484f1a2c8b8e4f3c8b8"
            }
        }


class DocumentTypeWithDepartment(DocumentTypeInDB):
    """Schema for document type with department details"""
    department: DepartmentInDB

    class Config:
        populate_by_name = True


class DocumentTypeResponse(DocumentTypeInDB):
    """Response schema for document type"""
    pass