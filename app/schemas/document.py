from typing import List, Optional
from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.schemas.base import PyObjectId

class Document(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
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
    )

class DocumentCreate(Document):
    title: str = Field(..., min_length=1, description="Document title")
    document_type_id: PyObjectId = Field(..., description="Reference to DocumentType ID")
    department_id: PyObjectId = Field(..., description="Reference to Department ID")
    created_by: Optional[str] = Field(None, description="User who created the document")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str},
        json_schema_extra={
            "example": {
                "created_by": "helloworld",
                "department_id": "682440853d6cd156e5585927",
                "document_type_id": "6825af3e13ad6fad9efe7d1d",
                "title": "Tender Proposal"
            }
        }
    )

class DocumentInDB(Document):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ref_no: str = Field(..., min_length=1, description="Unique reference number")
    title: str = Field(..., description="Document title")
    document_type_id: PyObjectId = Field(..., description="Reference to DocumentType ID")
    department_id: PyObjectId = Field(..., description="Reference to Department ID")
    created_by: str = Field(..., description="User who created the document")
    created_date: datetime = Field(..., description="Creation timestamp")
    filed_by: Optional[str] = Field(None, description="User who filed the document")
    filed_date: Optional[datetime] = Field(None, description="Filing timestamp")
    status: str = Field(default="Not Filed", description="Document status", pattern="^(Not Filed|Filed|Suspended)$")

    file_path: Optional[str] = Field(None, description="Relative path to the stored file")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()}
    )

class DocumentUpdateNormal(BaseModel):
    doc_id: PyObjectId = Form(..., description="Document ID to update")
    title: Optional[str] = Form(None, min_length=1, description="Document title")
    department_id: Optional[PyObjectId] = Form(None, description="Reference to Department ID")
    document_type_id: Optional[PyObjectId] = Form(None, description="Reference to DocumentType ID")
    file_path: Optional[str] = Field(None, description="Relative path to the stored file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doc_id": "682440853d6cd156e5585927",
                "title": "Updated Tender Proposal",
                "document_type_id": "6825af3e13ad6fad9efe7d1d",
                "department_id": "682440853d6cd156e5585927",
            }
        }
    )

class DocumentUpdateAdmin(DocumentUpdateNormal):
    doc_id: PyObjectId = Field(..., description="Document ID to update")
    created_date: Optional[datetime] = Form(None, description="Creation date of the document")
    created_by: Optional[str] = Form(None, min_length=1, description="User who created the document")
    filed_date: Optional[datetime] = Form(None, description="Filing date of the document")
    filed_by: Optional[str] = Form(None, min_length=1, description="User who filed the document")
    status: Optional[str] = Form(None, description="Document status", pattern="^(Not Filed|Filed|Suspended)$")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doc_id": "682440853d6cd156e5585927",
                "title": "Updated Tender Proposal",
                "document_type_id": "6825af3e13ad6fad9efe7d1d",
                "created_date": "2025-02-25T13:00:00Z",
                "created_by": "alvin",
                "filed_date": "2025-03-26T13:00:00Z",
                "filed_by": "nay",
                "status": "Filed",
            }
        }
    )

class BulkDeleteRequest(BaseModel):
    document_ids: List[PyObjectId] = Field(..., description="List of document IDs to delete")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str},
        json_schema_extra={
            "example": {
                "document_ids": [
                    "66488b368a6801e71d70dfe9",
                    "66488b368a6801e71d70dfea"
                ]
            }
        }
    )

class DocumentResponse(DocumentInDB):
    pass

class DocumentPaginationResponse(BaseModel):
    total: int = Field(..., description="Total number of documents matching the query")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Maximum number of documents per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    documents: List[DocumentInDB] = Field(..., description="List of documents in the current page")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda dt: dt.isoformat()},
        json_schema_extra={
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
    )

class BulkUpdateStatusRequest(BaseModel):
    document_ids: List[PyObjectId] = Field(..., description="List of document IDs to update")
    status: str = Field(..., description="New status for documents", pattern="^(Not Filed|Filed|Suspended)$")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str},
        json_schema_extra={
            "example": {
                "document_ids": [
                    "66488b368a6801e71d70dfe9",
                    "66488b368a6801e71d70dfea"
                ],
                "status": "Filed"
            }
        }
    )


class csvDocumentData(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    ref_no: Optional[str] = Field(None, min_length=1, description="Unique reference number")
    title: Optional[str] = Field(None, description="Document title")
    document_type_id: Optional[PyObjectId] = Field(None, description="Reference to DocumentType ID")
    department_id: Optional[PyObjectId] = Field(None, description="Reference to Department ID")
    created_by: Optional[str] = Field(None, description="User who created the document")
    created_date: Optional[datetime] = Field(None, description="Creation timestamp")
    filed_by: Optional[str] = Field(None, description="User who filed the document")
    filed_date: Optional[datetime] = Field(None, description="Filing timestamp")
    status: Optional[str] = Field(None, description="Document status", pattern="^(Not Filed|Filed|Suspended)$")
    file_id: Optional[PyObjectId] = None
    inserted_id: Optional[int] = Field(None, alias="inserted_id")