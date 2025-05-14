from typing import Optional
from pydantic import BaseModel, Field
from .base import PyObjectId
from .department import DepartmentInDB

class DocumentType(BaseModel):
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
   
    name: str = Field(..., min_length=1, description="Unique document type name (e.g., Tender Committee)")
    prefix: str = Field(..., min_length=1, description="Unique prefix for reference number (e.g., TPG)")
    department_id: PyObjectId = Field(..., description="Reference to Department")

class DocumentTypeInDB(DocumentType):
  
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., min_length=1, description="Unique document type name (e.g., Tender Committee)")
    prefix: str = Field(..., min_length=1, description="Unique prefix for reference number (e.g., TPG)")
    department_id: PyObjectId = Field(..., description="Reference to Department")

class DocumentTypeResponse(DocumentTypeInDB):
    pass

class DocumentTypeWithDepartment(DocumentTypeInDB):
    department: DepartmentInDB = Field(..., description="Associated Department details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Tender Committee",
                "prefix": "TPG",
                "department_id": "507f1f77bcf86cd799439013",
                "department": {
                    "_id": "507f1f77bcf86cd799439013",
                    "name": "Finance"
                }
            }
        }