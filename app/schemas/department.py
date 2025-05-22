from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.base import PyObjectId


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, description="Unique department name")
    created_date: Optional[datetime] = Field(None, description="Creation date")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={"example": {"name": "Finance"}}
    )


class DepartmentInDBMinimal(DepartmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

class DocumentType(BaseModel):
    name: str = Field(..., description="Name of the document type")
    prefix: str = Field(..., description="Prefix for document numbering")
    created_date: Optional[datetime] = Field(None, description="Creation date ")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={"example": {"name": "Invoice", "prefix": "INV"}}
    )

class DocumentTypeCreate(DocumentType):
    pass


class DocumentTypeInDB(DocumentType):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


class DocumentTypeWithDepartment(DocumentTypeInDB):
    department: DepartmentInDBMinimal = Field(..., description="Department details")


class DepartmentCreate(DepartmentBase):
    document_types: List[DocumentTypeCreate] = Field(default_factory=list, description="List of document types")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
            "example": {
                "name": "Finance",
                "document_types": [
                    {"name": "Invoice", "prefix": "INV"},
                    {"name": "Receipt", "prefix": "REC"}
                ]
            }
        }
    )


class DepartmentInDB(DepartmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    document_types: List[DocumentTypeInDB] = Field(default_factory=list, description="Embedded document types")


class DepartmentResponse(DepartmentInDB):
    pass
