from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.base import PyObjectId
# --- Department Schemas ---
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, description="Unique department name")
    full_name: Optional[str | None] = Field(None, description="Full name of the department")
    # 0 or 1 for active or inactive
    status: int = Field(..., ge=0, le=1, description="Status of the department (0: inactive, 1: active)")
    created_date: Optional[datetime] = Field(None, description="Creation date")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={"example": {"name": "TPG"}}
    )


class DepartmentInDBMinimal(DepartmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


# --- DocumentType Schemas ---
class DocumentType(BaseModel):
    name: str = Field(..., description="Name of the document type")
    prefix: str = Field(..., description="Prefix for document numbering")
    padding: int = Field(..., ge=1, description="Number of digits for document numbering")
    counters: Dict[str, int] = Field(default_factory=dict, description="Year-to-sequence mapping for document numbering")
    created_date: Optional[datetime] = Field(None, description="Creation date")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
            "example": {
                "name": "Tender Committee",
                "prefix": "TPG-TC",
                "padding": 2,
                "counters": {"2025": 100},
                "created_date": "2024-10-08T12:41:53.000Z"
            }
        }
    )


class DocumentTypeCreate(BaseModel):
    name: str = Field(..., description="Name of the document type")
    prefix: str = Field(..., description="Prefix for document numbering")
    padding: int = Field(..., ge=1, description="Number of digits for document numbering")
    counters: Optional[Dict[str, int]] = Field(default=None, description="Optional year-to-sequence mapping")
    created_date: Optional[datetime] = Field(None, description="Creation date")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
            "example": {
                "name": "Tender Committee",
                "prefix": "TPG-TC",
                "padding": 2,
                "counters": {"2025": 100},
                "created_date": "2024-10-08T12:41:53.000Z"
            }
        }
    )


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
                "name": "TPG",
                "status": 1,
                "document_types": [
                    {
                        "name": "Tender Committee",
                        "prefix": "TPG-TC",
                        "padding": 2,
                        "counters": {"2025": 100}
                    },
                    {
                        "name": "Chairman",
                        "prefix": "TPG-CH",
                        "padding": 2,
                        "counters": {"2025": 5}
                    }
                ]
            }
        }
    )


class DepartmentInDB(DepartmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    document_types: List[DocumentTypeInDB] = Field(default_factory=list, description="Embedded document types")


class DepartmentResponse(DepartmentInDB):
    pass


class DepartmentStatusUpdate(BaseModel):
    departments: List[str]
    status: int

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
            "example": {
                "departments": ["TPU, TPG"],
                "status": 1
            }
        }
    )

class csvDocumentType(BaseModel):
    inserted_id: Optional[int] = Field(None, description="Custom ID for the document type")
    name: str = Field(..., description="Document type name")
    prefix: str = Field(..., description="Prefix for document numbering")
    padding: int = Field(..., ge=1, description="Number of digits for document numbering")
    counters: Optional[Dict[str, int]] = Field(default=None, description="Optional year-to-sequence mapping")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
            "example": {
                "name": "Tender Committee",
                "prefix": "TPG-TC",
                "padding": 2,
                "counters": {"2025": 100}
            }
        }
    )

class csvDepartment(BaseModel):
    name: str = Field(..., description="Department name")
    inserted_id: Optional[int] = Field(None, description="Custom ID for the department")
    document_types: List[csvDocumentType] = Field(default_factory=list, description="List of document types")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
            "example": {
                "name": "TPG",
                "document_types": [
                    {
                        "name": "Tender Committee",
                        "prefix": "TPG-TC",
                        "padding": 2
                    }
                ]
            }
        }
    )

