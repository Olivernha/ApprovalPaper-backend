from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
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
    document_type_id: PyObjectId = Field(..., description="Reference to DocumentType ID")
    department_id: PyObjectId = Field(..., description="Reference to Department ID")
    created_by: str = Field(..., description="User who created the document")
    created_date: datetime = Field(..., description="Creation timestamp")
    filed_by: Optional[str] = Field(None, description="User who filed the document")
    filed_date: Optional[datetime] = Field(None, description="Filing timestamp")
    status: str = Field(default="Not Filed", description="Document status", pattern="^(Not Filed|Filed|Suspended)$")
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda dt: dt.isoformat()}

class DocumentUpdateNormal(BaseModel):
    """Schema for normal user document update."""
    title: Optional[str] = Field(None, min_length=1, description="Document title")
    department_id: Optional[PyObjectId] = Field(None, description="Reference to Department ID")
    document_type_id: Optional[PyObjectId] = Field(None, description="Reference to DocumentType ID")
    current_user: Optional[str] = Field(None, description="Current user making the update")
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Tender Proposal",
                "document_type_id": "6825af3e13ad6fad9efe7d1d",
                "current_user": "helloworld",
                "department_id": "682440853d6cd156e5585927"
            }
        }

class DocumentUpdateAdmin(DocumentUpdateNormal):
    """Schema for admin document update."""
    created_date: Optional[str] = Field(None, description="Creation date in DD/MM/YYYY format")
    created_by: Optional[str] = Field(None, min_length=1, description="User who created the document")
    filed_date: Optional[str] = Field(None, description="Filing date in DD/MM/YYYY format")
    filed_by: Optional[str] = Field(None, min_length=1, description="User who filed the document")
    status: Optional[str] = Field(None, description="Document status", pattern="^(Not Filed|Filed|Suspended)$")
    @field_validator("created_date", "filed_date")
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Date must be in DD/MM/YYYY format")
        return v
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Tender Proposal",
                "document_type_id": "6825af3e13ad6fad9efe7d1d",
                "created_date": "25/02/2026",
                "created_by": "alvin",
                "filed_date": "26/03/2026",
                "filed_by": "nay",
                "status": "Filed",
                "current_user": "admin_user"
            }
        }

class DocumentDelete(BaseModel):
    """Schema for deleting a document."""
    current_user: str = Field(..., description="User who is deleting the document")

class DocumentResponse(DocumentInDB):
    """Schema for API responses."""
    pass

class DocumentPaginationResponse(BaseModel):
    """Schema for paginated document responses."""
    total: int = Field(..., description="Total number of documents matching the query")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Maximum number of documents per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    documents: List[DocumentInDB] = Field(..., description="List of documents in the current page")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda dt: dt.isoformat()}
        json_schema_extra = {
            "example": {
                "total": 25,
                "page": 1,
                "limit": 10,
                "pages": 3,
                "has_next": True,
                "has_prev": False,
                "documents": [
                    {
                        "_id": "66488b368a6801e71d70dfe9",
                        "ref_no": "IT/001/25",
                        "title": "Tender Proposal",
                        "document_type_id": "6825af3e13ad6fad9efe7d1d",
                        "department_id": "682440853d6cd156e5585927",
                        "created_by": "helloworld",
                        "created_date": "2025-05-15T13:00:00Z",
                        "status": "Not Filed"
                    }
                ]
            }
        }

class BulkDeleteRequest(BaseModel):
    """Schema for bulk deleting documents."""
    document_ids: List[PyObjectId] = Field(..., description="List of document IDs to delete")
    current_user: str = Field(..., description="Admin user performing the bulk delete")
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "document_ids": [
                    "66488b368a6801e71d70dfe9",
                    "66488b368a6801e71d70dfea"
                ],
                "current_user": "admin_user"
            }
        }

class BulkUpdateStatusRequest(BaseModel):
    """Schema for bulk updating document statuses."""
    document_ids: List[PyObjectId] = Field(..., description="List of document IDs to update")
    status: str = Field(..., description="New status for documents", pattern="^(Not Filed|Filed|Suspended)$")
    current_user: str = Field(..., description="Admin user performing the bulk update")
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "document_ids": [
                    "66488b368a6801e71d70dfe9",
                    "66488b368a6801e71d70dfea"
                ],
                "status": "Filed",
                "current_user": "admin_user"
            }
        }