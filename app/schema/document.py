from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .base import PyObjectId

class Document(BaseModel):
    """Base class for document models."""
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda dt: dt.isoformat()}
        json_schema_extra = {
            "example": {
                "ref_no": "IT/001/25",
                "title": "Tender Proposal",
                "document_type_id": "507f1f77bcf86cd799439011",
                "department_id": "507f1f77bcf86cd799439013",
                "created_by": "helloworld",
                "created_date": "2025-05-15T13:00:00Z",
                "status": "Not Filed"
            }
        }

class DocumentCreate(Document):
    """Schema for creating a new document."""
    title: str = Field(..., min_length=1, description="Document title")
    document_type_id: PyObjectId = Field(..., description="Reference to DocumentType ID")
    department_id: PyObjectId = Field(..., description="Reference to Department ID")
    created_by: str = Field(..., description="User who created the document")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "created_by": "helloworld",
                "department_id": "682440853d6cd156e5585927",
                "document_type_id": "6825af3e13ad6fad9efe7d1d",
                "title": "Tender Proposal"
            }
        }

class DocumentInDB(Document):
    """Schema for MongoDB document (includes _id)."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ref_no: str = Field(..., min_length=1, description="Unique reference number")
    title: str = Field(..., min_length=1, description="Document title")
    document_type_id: PyObjectId = Field(..., description="Reference to DocumentType ID")  # Changed to PyObjectId
    department_id: PyObjectId = Field(..., description="Reference to Department ID")  # Changed to PyObjectId
    created_by: str = Field(..., description="User who created the document")
    created_date: datetime = Field(..., description="Creation timestamp")
    filed_by: Optional[str] = Field(None, description="User who filed the document")
    filed_date: Optional[datetime] = Field(None, description="Filing timestamp")
    status: str = Field(default="Not Filed", description="Document status", pattern="^(Not Filed|Filed|Suspended)$")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda dt: dt.isoformat()}

class DocumentResponse(DocumentInDB):
    """Schema for API responses."""
    pass