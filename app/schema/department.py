from typing import List, Optional
from pydantic import BaseModel, Field

from . import DocumentTypeCreate, DocumentTypeInDB
from .base import PyObjectId
class Department(BaseModel):
    """Base department model"""
    name: str = Field(..., min_length=1, description="Unique department name")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Finance"
            }
        }
class DepartmentBase(Department):
    id : PyObjectId = Field(default_factory=PyObjectId, alias="_id")
class DepartmentCreate(Department):
    """Schema for creating a department"""
    document_types: List[DocumentTypeCreate] = Field(default_factory=list, description="List of document types")

    class Config(Department.Config):
        json_schema_extra = {
            "example": {
                "name": "Finance",
                "document_types": [
                    {
                        "name": "Invoice",
                        "prefix": "INV"
                    },
                    {
                        "name": "Receipt",
                        "prefix": "REC"
                    }
                ]
            }
        }

class DepartmentInDB(Department):
    """Schema for department in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    document_types: List[DocumentTypeInDB] = Field(default_factory=list, description="Embedded document types")



class DocumentTypeWithDepartment(DocumentTypeInDB):
    department : DepartmentBase = Field(..., description="Department details")


class DepartmentResponse(DepartmentInDB):
    """Schema for department response"""
    pass